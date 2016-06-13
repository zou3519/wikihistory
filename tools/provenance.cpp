/*
 * provenance.cpp
 * Addressing Underspecified Lineage Queries on Provenance
 *
 * Copyright 2009
 *      The President and Fellows of Harvard College.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE UNIVERSITY AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE UNIVERSITY OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 *
 * Contributor(s): Peter Macko
 */

#include "stdafx.h"
#include "provenance.h"

#include "twig.h"
#include "twig_file.h"

#include <fnmatch.h>
#include <vector>

#ifdef __GNUC__
#include <ext/hash_map>
#else
#include <hash_map>
#endif

#include <fstream>
#include <iostream>

using namespace __gnu_cxx;
using namespace std;


bool hideCells = false;
bool collapseVersions = false;

hash_map_llu map;
hash_map_str files;
std::vector<Node*> nodes;

unsigned long long maxfd = 0;


#define LARGE_BUF_SIZE 81920


/**
 * Initialize a node
 *
 * @param node the node
 */
void InitNode(Node& node)
{
	static int _uid = 0;

	node.name = node.type = node.pid = "";
	node.prev = node.next = NULL;
	node.visible = true;

	node.numInputs = 0;
	node.numOutputs = 0;

	node.pagerank = 0;
	node.provrank = 0;
	node.subrank = 0;

	node.uid = _uid++;
}


/**
 * Load a twig provenance record
 *
 * @param rec the twig provenance record
 * @param anc_pass whether this is an ancestry pass
 * @return the error code, or 0 if no errors occurred
 */
int LoadRecord(const struct twig_precord* rec, bool anc_pass)
{
	const char *attr_val = TWIG_PRECORD_ATTRIBUTE(rec);
	int attr_len = rec->tp_attrlen; assert(attr_len < 24);
	char attr[24]; memcpy(attr, attr_val, attr_len);
	attr[attr_len] = '\0';

	const void *value = TWIG_PRECORD_VALUE(rec);
	int type = rec->tp_valuetype;
	//bool anc = rec->tp_flags & PROV_IS_ANCESTRY;

	unsigned long long desc_fd = rec->tp_pnum;
	unsigned desc_ver = rec->tp_version;
	if (collapseVersions) desc_ver = 0;
	unsigned long long desc_key = (desc_fd << 16) | (unsigned long long) desc_ver;


	// Get the hashmap node, or create it if it is not found

	hash_map_llu::iterator itr = map.find(desc_key);
	Node& e = map[desc_key];
	assert(itr != map.end());


	// Convert the value to string

	static char buffer[LARGE_BUF_SIZE];
	char* buf = buffer;
	buf[0] = '\0';

	const struct prov_pnodeversion *ppv;
	const char *valuestr;
	uint32_t total;
	const struct prov_timestamp *pts;

	bool ignore = anc_pass;

	switch (type) {

		case PROV_TYPE_NIL:
			sprintf(buf, "(nil)");
			break;

		case PROV_TYPE_STRING:
			valuestr = (const char*) value;
			snprintf(buf, LARGE_BUF_SIZE, "%.*s", rec->tp_valuelen, valuestr);
			break;

		case PROV_TYPE_MULTISTRING:
			valuestr = (const char*) value;
			total = 0;
			while (total < rec->tp_valuelen) {
				size_t len = strlen(valuestr + total) + 1;
				assert(total + len < LARGE_BUF_SIZE);
				strcat(buf, valuestr + total);
				strcat(buf, " ");
				total += len;
			}
			break;

		case PROV_TYPE_INT:
			sprintf(buf, "%d", (int)*(int32_t *)value);
			break;

		case PROV_TYPE_REAL:
			sprintf(buf, "%g", *(double *)value);
			break;

		case PROV_TYPE_TIMESTAMP:
			pts = (const struct prov_timestamp*) value;
			sprintf(buf, "%u.%09u", (unsigned)(pts->pt_sec), (unsigned)(pts->pt_nsec));
			break;

		case PROV_TYPE_INODE:
			sprintf(buf, "%u", (unsigned)*(uint32_t *)value);
			break;

		case PROV_TYPE_PNODEVERSION:
		{
			ignore = !anc_pass;
			if (!ignore) {
				ppv = (const struct prov_pnodeversion*) value;
				unsigned ppv_ver = (unsigned)(ppv->version);
				if (collapseVersions) ppv_ver = 0;
				unsigned long long key = ((unsigned long long)(ppv->pnode) << 16) | ppv_ver;
				hash_map_llu::iterator itr2 = map.find(key);
				Node& a = map[key];
				if (itr2 == map.end()) {
					InitNode(a);
					sprintf(buf, "%lld.%d", (long long) ppv->pnode, ppv_ver);
					Attribute at;
					at.name = "TYPE";
					at.value = "UNKNOWN";
					a.attr.push_back(at);
					a.pnode = (unsigned long long) ppv->pnode;
					a.version = ppv_ver;
					a.item = buf;
				}

				sprintf(buf, "%s", a.item.c_str());
				if (e.pnode == a.pnode) {
					//fprintf(stderr, "Warning: Ignoring a self-loop at %lld.%lld\n", (long long) desc_fd, (long long) desc_ver);
					return 0;
				}

				bool ok = true;

				for (int i = 0; i < e.inputs.size(); i++) {
					if (e.inputs[i] == &a) {
						ok = false;
						break;
					}
				}

				if (noZeroVersions && ok) {
					if (a.version == 0 && ok) {
						ok = false;
						for (int i = 0; i < a.attr.size(); i++) {
							if (a.attr[i].name == "TYPE") {
								if (a.attr[i].value == "NP_FILE") ok = true;
								break;
							}
						}
					}
					if (e.version == 0 && ok) {
						ok = false;
						for (int i = 0; i < e.attr.size(); i++) {
							if (e.attr[i].name == "TYPE") {
								if (e.attr[i].value == "NP_FILE") ok = true;
								break;
							}
						}
					}
				}

				if (ok) {
					e.inputs.push_back(&a);
					a.outputs.push_back(&e);
				}
			}
			break;
		}

		case PROV_TYPE_OBJECT:
		case PROV_TYPE_OBJECTVERSION:
			assert(0);
			break;

		default:
			assert(0);
			break;
	}


	// Add the attribute

	if (!ignore) {
		Attribute a;
		a.name = attr;
		a.value = buf;
		e.attr.push_back(a);
	}

	return 0;
}


/**
 * Load a twig file
 *
 * @param inputFilename the file name
 * @return the error code, or 0 if no errors occurred
 */
int LoadTwig(const char* inputFilename)
{
	int r;


	// Build the object map

	struct twig_file* file = twig_open(inputFilename, TWIG_RDONLY);
	if (file == NULL) {
		fprintf(stderr, "Failed to open\n");
		return -1;
	}
	struct twig_rec* rec = NULL;
	while (twig_read(file, &rec) != EOF) {
		if ((enum twig_rectype) rec->rectype == TWIG_REC_PROV) {
			struct twig_precord *pr = (struct twig_precord *)rec;
			unsigned long long desc_fd = pr->tp_pnum;
			if (desc_fd > maxfd) maxfd = desc_fd;
			unsigned desc_ver = pr->tp_version;
			if (collapseVersions) desc_ver = 0;
			unsigned long long desc_key = (desc_fd << 16) | (unsigned long long) desc_ver;
			hash_map_llu::iterator itr = map.find(desc_key);
			if (itr == map.end()) {
				char buf[512];
				sprintf(buf, "%lld.%u", desc_fd, desc_ver);
				Node& e = map[desc_key];
				if (collapseVersions && !e.attr.empty()) continue;
				assert(e.attr.empty());
				InitNode(e);
				e.pnode = (unsigned long long) desc_fd;
				e.item = buf;
				e.version = (unsigned long) desc_ver;
			}
		}
	}
	twig_close(file);


	// Open the file

	file = twig_open(inputFilename, TWIG_RDONLY);
	if (file == NULL) {
		fprintf(stderr, "Failed to open\n");
		return -1;
	}


	// Main loop

	rec = NULL;
	while (twig_read(file, &rec) != EOF) {


		// Handle different kinds of records

		enum twig_rectype type = (enum twig_rectype) rec->rectype;
		switch (type) {

			case TWIG_REC_PROV:
				r = LoadRecord((struct twig_precord *)rec, false);
				break;

			default:
				r = 0;
				break;
		}


		// Exit on error

		if (r != 0) {
			fprintf(stderr, "Failed\n");
			twig_close(file);
			return r;
		}
	}


	// Close the file

	twig_close(file);


	// Open the file

	file = twig_open(inputFilename, TWIG_RDONLY);
	if (file == NULL) {
		fprintf(stderr, "Failed to open\n");
		return -1;
	}


	// Main loop

	rec = NULL;
	while (twig_read(file, &rec) != EOF) {


		// Handle different kinds of records

		enum twig_rectype type = (enum twig_rectype) rec->rectype;
		switch (type) {

			case TWIG_REC_PROV:
				r = LoadRecord((struct twig_precord *)rec, true);
				break;

			default:
				r = 0;
				break;
		}


		// Exit on error

		if (r != 0) {
			fprintf(stderr, "Failed\n");
			twig_close(file);
			return r;
		}
	}


	// Close the file

	twig_close(file);

	return 0;
}


/**
 * Finalize loading and build in-memory indexes
 */
void FinalizeLoading(void)
{
	// Rename the objects

	for (hash_map_llu::iterator itr = map.begin(); itr != map.end(); itr++) {
		std::vector<Attribute>& attr = itr->second.attr;

		// Find NAME, TYPE, and ARGV

		std::string name = "";
		std::string type = "";
		std::string argv = "";
		std::string pid  = "";

		for (int i = 0; (i < attr.size()) && (name == "" || type == ""); i++) {
			if (attr[i].name == "NAME") name = attr[i].value;
			if (attr[i].name == "TYPE") type = attr[i].value;
			if (attr[i].name == "ARGV") argv = attr[i].value;
			if (attr[i].name == "PID" ) pid  = attr[i].value;
		}

		if (itr->second.name == "") itr->second.name = name;
		if (itr->second.type == "") itr->second.type = type;

		if (name == "" && type == "") continue;

		if (type == "CELL" && name == "") {
			std::string table = "";
			std::string row = "";
			std::string column = "";

			for (int i = 0; (i < attr.size()) && (name == "" || type == ""); i++) {
				if (attr[i].name == "TABLE" ) table  = attr[i].value;
				if (attr[i].name == "ROW"   ) row    = attr[i].value;
				if (attr[i].name == "COLUMN") column = attr[i].value;
			}

			name = table;
			if (name != "") name += " ";

			name = name + row + ":" + column;
			if (name == ":") name = "";
		}

		if (argv != "") if (argv[argv.length() - 1] == ' ') argv = argv.substr(0, argv.length() - 1);

		unsigned long long int fd = (itr->first >> 16);
		int count = 25;
		for (int i = 0; ; i++) {
			if (map.find((fd << 16) | i) == map.end()) {
				if (count --> 0) continue; else break;
			}
			Node& e = map[(fd << 16) | i];
			if (e.name == "") e.name = name;
			if (e.type == "") e.type = type;
			if (e.args == "") e.args = argv;
			if (e.pid  == "") e.pid  = pid ;
		}
	}


	// Hide cells, if configured to do so

	if (hideCells) {
		for (hash_map_llu::iterator itr = map.begin(); itr != map.end(); itr++) {
			Node& e = itr->second;
			if (e.type == "CELL") e.visible = false;
		}
	}


	// Do the next/prev links

	for (int fd = 1; fd <= maxfd; fd++) {
		for (int i = 1; map.find((fd << 16) | i) != map.end(); i++) {
			Node& e = map[(fd << 16) | i];
			Node& p = map[(fd << 16) | (i - 1)];
			e.prev = &map[(fd << 16) | (i - 1)];
			p.next = &map[(fd << 16) | (i)];
		}
	}


	// Get the list of files

	for (hash_map_llu::iterator itr = map.begin(); itr != map.end(); itr++) {
		if (itr->second.type == "" || itr->second.name == "" || itr->second.next != NULL) continue;
		if (itr->second.type == "FILE") files[itr->second.name] = &itr->second;
	}


	// Get the list of all nodes

	for (hash_map_llu::iterator itr = map.begin(); itr != map.end(); itr++) {
		nodes.push_back(&itr->second);
	}


	// Add extra version links

	if (!collapseVersions && linkVersions) {
		for (hash_map_llu::iterator itr = map.begin(); itr != map.end(); itr++) {
			if (itr->second.next != NULL) continue;

			int fd = itr->second.pnode;
			int low = noZeroVersions ? 1 : 0;
			for (int i = low; map.find(Key(fd, i)) != map.end(); i++) {
				Node& e = map[Key(fd, i)];
				if (e.prev != NULL && i > low) e.inputs.push_back(e.prev);
				if (e.next != NULL) e.outputs.push_back(e.next);
			}
		}
	}
}


/**
 * Return a node name
 *
 * @param n the node
 * @param withPNode whether to include the pnode
 * @param alignPNode whether to align
 * @return the node name
 */
std::string NodeName(Node* n, bool withPNode, bool alignPNode)
{
	std::string s = "";

	if (withPNode) {

		if (alignPNode) {
			if (n->pnode <    10) s += " ";
			if (n->pnode <   100) s += " ";
			if (n->pnode <  1000) s += " ";
			if (n->pnode < 10000) s += " ";
		}

		char buf[64];
		sprintf(buf, "%lld.%ld", n->pnode, n->version);
		s += buf;

		if (alignPNode && !collapseVersions) {
			if (n->version <  10) s += " ";
			if (n->version < 100) s += " ";
		}

		s += " ";
	}

	if (n->type == "PIPE") s += "[PIPE] ";

	if (n->type == "PROC") {
		if (n->args != "") {
			std::string a = n->args;
			if (a.length() > 64) a = a.substr(0, 64) + "...";
			s += a;
		}
		else {
			s += n->name != "" ? n->name : n->item;
		}
		s += " (PID " + n->pid + ")";
	}
	else {
		s += n->name != "" ? n->name : n->item;
	}

	return s;
}


/**
 * Get a node based on the string argument
 *
 * @param str the string argument
 * @return the node, or NULL if not found
 */
Node* Lookup(const char* str)
{
	// Interpret str as a file name

	hash_map_str::iterator i = files.find(std::string(str));
	if (i != files.end()) return i->second;


	// Try to interpret it as a search pattern if it has * or ?

	if (strchr(str, '*') != NULL || strchr(str, '?') != NULL) {
		Node* n = NULL;

		for (int ni = 0; ni < nodes.size(); ni++) {
			if (nodes[ni]->next != NULL) continue;
			if (nodes[ni]->type != "FILE" && nodes[ni]->type != "NP_FILE") continue;

			if (fnmatch(str, nodes[ni]->name.c_str(), 0) == 0) {
				if (n != NULL) {

					// Return NULL if the pattern matches more than one result
					if (n->pnode != nodes[ni]->pnode) return NULL;

					// If we matched a more recent version, choose that one
					if (n->version < nodes[ni]->version) n = nodes[ni];
				}
				else {
					n = nodes[ni];
				}
			}
		}

		return n;
	}


	// Otherwise interpret it as pnode.version

	char* s = (char*) alloca(std::strlen(str) + 4);
	strcpy(s, str);

	char* ver = NULL;
	for (char* p = s; *p != '\0'; p++) {
		if (isdigit(*p)) continue;
		if (*p == '.') {
			ver = p + 1;
			*p = '\0';

			for (char* q = ver; *q != '\0'; q++) {
				if (isdigit(*q)) continue;
				return NULL;
			}
			break;
		}
		return NULL;
	}

	unsigned long pnode = atoi(s);
	unsigned int version = atoi(ver);

	hash_map_llu::iterator j = map.find(Key(pnode, version));
	if (j != map.end()) return &(j->second);

	return NULL;
}

/**
 * Dump the graph to a CSV format.
 *
 * @param filename The filename to dump to.
 */
void DumpCSV(const char* filename)
{
    ofstream f;
    f.open(filename, ios::trunc);

    // Dump nodes.
    for(hash_map_llu::iterator i = map.begin(); i != map.end(); i++)
    {
        Node n = i->second;
        f << n.pnode << '.' << n.version << ',' << n.provrank << ',' << n.subrank << ',' << n.name << '\n';
    }

    f << '\n';

    for(hash_map_llu::iterator i = map.begin(); i != map.end(); i++)
    {
        Node u = i->second;
        for(int j = 0; j < u.inputs.size(); j++)
        {
            Node* v = u.inputs[j];
            f << u.pnode << '.' << u.version << ',' << v->pnode << '.' << v->version << '\n';
        }
    }

    f.close();
}
