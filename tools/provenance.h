/*
 * provenance.h
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

#ifndef __PROVENANCE_H__
#define __PROVENANCE_H__

#include <string>
#include <vector>

#ifdef __GNUC__
#include <ext/hash_map>
#else
#include <hash_map>
#endif

#include "util.h"

using namespace __gnu_cxx;


typedef struct {
	std::string name;
	std::string value;
} Attribute;


/*
 * Compatison function for the hash map
 */
struct eqllu { bool operator()(unsigned long long a, unsigned long long b) { return a == b; } };


/*
 * Hash function for the hash map
 */
struct hllu {
	hash<unsigned long> hlu;
	size_t operator()(unsigned long long register a) const
	{
		return hlu((unsigned long) (((a >> 8) & 0xffffff00) | (a & 0xff)));
	}
};


/*
 * Compatison function for the hash map
 */
struct eqstr { bool operator()(const std::string& a, const std::string& b) { return a == b; } };


/*
 * Hash function for the hash map
 */
struct hstr {
	hash<const char*> hcs;
	size_t operator()(const std::string& a) const
	{
		return hcs(a.c_str());
	}
};


#define ITEM_NAME_SIZE 512

/*
 * A graph node
 */
typedef struct _Node {

	unsigned long long pnode;
	unsigned long version;

	bool visible;
	long uid;


	// ==================== Node Attributes =====================

	std::vector<Attribute> attr;

	std::string item;
	std::string name;
	std::string type;
	std::string args;
	std::string pid;


	// =================== Node Relationships ===================

	struct _Node* prev;
	struct _Node* next;

	std::vector<struct _Node*> inputs;
	std::vector<struct _Node*> outputs;


	// ============== Optionally calculated fields ==============

	// Total number of inputs and outputs (not just immediate)

	int numInputs;
	int numOutputs;
	hash_set_ptr allInputs;


	// Ranks

	long double pagerank;
	long double provrank;
	long double subrank;


	// ============= Temportary & Intermediate Data =============

	long double aux;

} Node;


/**
 * Create a key for the pnode.version pair
 *
 * @param pnode the pnode
 * @param version the version
 */
inline unsigned long long Key(unsigned long long pnode, unsigned int version) {
	return (pnode << 16) | (unsigned long long) version;
}


/**
 * Create a key for the given node
 *
 * @param node the node
 */
inline unsigned long long Key(const Node* node) {
	return Key(node->pnode, node->version);
}


/*
 * Compatison function for the hash map
 */
struct eqnode { bool operator()(const Node* a, const Node* b) const { return Key(a) == Key(b); } };


/*
 * Hash function for the hash map
 */
struct hnode {
	hash<unsigned long> hlu;
	size_t operator()(const Node* node) const
	{
		unsigned long long register a = Key(node);
		return hlu((unsigned long) (((a >> 8) & 0xffffff00) | (a & 0xff)));
	}
};


/*
 * Hash maps
 */
typedef hash_map<unsigned long long, Node, hllu, eqllu> hash_map_llu;
typedef hash_map<std::string, Node*, hstr, eqstr> hash_map_str;


/*
 * Provenance graph
 */
extern hash_map_llu map;
extern hash_map_str files;
extern std::vector<Node*> nodes;


/*
 * Configuration
 */
extern bool hideCells;
extern bool collapseVersions;


/**
 * Load a twig file
 *
 * @param inputFilename the file name
 * @return the error code, or 0 if no errors occurred
 */
int LoadTwig(const char* inputFilename);


/**
 * Finalize loading and build in-memory indexes
 */
void FinalizeLoading(void);


/**
 * Return a node name
 *
 * @param n the node
 * @param withPNode whether to include the pnode
 * @param alignPNode whether to align
 * @return the node name
 */
std::string NodeName(Node* n, bool withPNode = false, bool alignPNode = false);


/**
 * Get a node based on the string argument
 *
 * @param str the string argument
 * @return the node, or NULL if not found
 */
Node* Lookup(const char* str);


/**
 * Dump the graph to a CSV format.
 *
 * @param filename The filename to dump to.
 */
void DumpCSV(const char* filename);


#endif
