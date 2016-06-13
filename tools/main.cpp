/*
 * main.cpp
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

#include <fnmatch.h>

#include "ancestry.h"
#include "parameters.h"
#include "provenance.h"
#include "webalgorithm.h"


/*
 * Configuration
 */
bool verbose = false;
bool linkVersions = true;
bool markMore = false;
bool noZeroVersions = true;

#ifdef _MAC
std::string svgApp = "Firefox";
#else
std::string svgApp = "firefox";
#endif


/**
 * Print the usage information
 *
 * @param name the program name
 */
void usage(const char* name)
{
	fprintf(stderr, "Usage: %s [OPTION]... INPUT_TWIG...\n\n", name);
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "  -a cmd   use the given application for viewing .svg files\n");
	fprintf(stderr, "  -c cmd   run the given ancestry command\n");
	fprintf(stderr, "  -C       collapse all node versions\n");
	fprintf(stderr, "  -h       print this help message\n");
	fprintf(stderr, "  -p       do not link node versions (treat them as patches)\n");
	fprintf(stderr, "  -P       precompute ProvRank\n");
	fprintf(stderr, "  -R       precompute PageRank\n");
	fprintf(stderr, "  -S       precompute SubRank\n");
	fprintf(stderr, "  -v       verbose output\n");
	fprintf(stderr, "  -z       include zero versions in lineage\n");
}


/**
 * Graphviz output
 *
 * @param r the result
 * @param flags the display flags
 */
void Graphviz(AncestryResult* r, int flags)
{
	std::string fname = "/tmp/cs222.dot";
	FILE* f = fopen(fname.c_str(), "w");

	if (f != NULL) {
		r->PrintGraphviz(f, flags);
		fclose(f);

		std::string cmd = "dot -Tsvg ";
		cmd += fname;
		cmd += " > ";
		cmd += fname;
		cmd += ".svg && ";
#ifdef _MAC
		cmd += "open -a ";
#else
		cmd += "(";
#endif
		cmd += svgApp;
		cmd += " ";
		cmd += fname;
		cmd += ".svg";
#ifndef _MAC
		cmd += " &)";
#endif

		int r = system(cmd.c_str());
		(void) r;
	}
	else {
		fprintf(stderr, "Error: Unable to create %s", fname.c_str());
	}
}


/**
 * Graphviz output
 *
 * @param r the result
 * @param file the file name
 * @param format the format
 * @param flags the display flags
 */
void Graphviz(AncestryResult* r, const char* file, const char* format, int flags)
{
	if (file == NULL || *file == '\0') {
		Graphviz(r, flags);
		return;
	}

	std::string fname = "/tmp/cs222.dot";
	FILE* f = fopen(fname.c_str(), "w");

	if (f != NULL) {
		r->PrintGraphviz(f, flags);
		fclose(f);

		std::string cmd = "dot -T";
		cmd += format;
		cmd += " ";
		cmd += fname;
		cmd += " > ";
		cmd += file;

		int r = system(cmd.c_str());
		(void) r;
	}
	else {
		fprintf(stderr, "Error: Unable to create %s", fname.c_str());
	}
}


/**
 * Statistics output
 *
 * @param r the result
 */
void Statistics(AncestryResult* r)
{
	fprintf(stdout, "Number of nodes: %d\n", r->CountNodes());
}


/**
 * Print the standard command options
 */
void PrintOptions(void)
{
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "  a=?, algorithm=?     The algorithm (ProvRank, SubRank, etc.)\n");
	fprintf(stderr, "  b=?, base=?          Whether to use ranks relative to the base\n");
	fprintf(stderr, "  c=?, cutoff=?        Cutoff when reaching the given value\n");
	fprintf(stderr, "  d=?, display=?       The display flags: [P]node, [R]ank, [I]ndegree, [O]utdegree\n");
	fprintf(stderr, "  j=?, cutoff-jump=?   Cutoff at the particular jump in rank\n");
	fprintf(stderr, "  m=?, cutoff-mult=?   Cutoff when reaching the given multiple of initial rank\n");
	fprintf(stderr, "  n=?, npfiles=?       Whether to include non-provenance files in the output\n");
	fprintf(stderr, "  o=?, output=?        Set the output method (Graphviz, text, etc.)\n");
	fprintf(stderr, "  r=?, recursive=?     Whether to answer queries recursively\n");
	fprintf(stderr, "  s=?, summarize=?     Whether to summarize the output graph\n");
	fprintf(stderr, "  S=?, stop=?          Stopping criterium (normal, thumb)\n");
	fprintf(stderr, "  t=?, traversal=?     The order of graph traversal (Breadth, Best, Worst)\n");
	fprintf(stderr, "  u=?, cutoff-mean=?   Cutoff when reaching the given multiple of cluster mean\n");
}


/**
 * Run a command line
 *
 * @param str_line the command line
 * @return true if the program should continue
 */
bool command(const char* str_line)
{
	if (str_line == NULL) { printf("\n"); return false; }
	if (*str_line == '\0') return true;

	std::string line = str_line;
	std::vector<std::string> args;
	Split(line, args);
	std::string cmd = args[0];
	args.erase(args.begin());


	// Command: Exit

	if (cmd == "q" || cmd == "quit") return false;


	// Help

	if (cmd == "h" || cmd == "?" || cmd == "help") {
		if (args.size() > 1) {
			fprintf(stderr, "Error: Invalid number of arguments\n");
			fprintf(stderr, "Usage: help [COMMAND]\n");
			return true;
		}

		std::string c = args.size() == 0 ? "help" : args[1];
		if (c == "h" || c == "?" || c == "help") {
			fprintf(stderr, "Commands and their shortcuts:\n");
			fprintf(stderr, "  a    ancestors     Get the graph of ancestors of the given p-node\n");
			fprintf(stderr, "  b    best          Print the p-nodes with the top scores\n");
			fprintf(stderr, "  d    descendants   Get the graph of descendants of the given p-node\n");
			fprintf(stderr, "  def  defaults      Print or set the default parameters used by other commands\n");
			fprintf(stderr, "  h    help          Print this help message\n");
			fprintf(stderr, "  p    print         Print the score of the given p-node\n");
			fprintf(stderr, "  q    quit          Quit the program\n");
			fprintf(stderr, "  r    range         Get statistics of ancestry graphs for a parameter range\n");
			fprintf(stderr, "  rd   range_desc    Get statistics of descendant graphs for a parameter range\n");
			fprintf(stderr, "  s    search        Search the provenance node names (files or processes)\n");
			fprintf(stderr, "\nTo obtain more information about a particular command, use: help [COMMAND]\n");
			return true;
		}

		if (c == "p" || c == "print") {
			fprintf(stderr, "Print the score associated with the given p-node\n");
			fprintf(stderr, "\nUsage: print FILE_NAME|NODE\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  print /untar/linux-2.6.19.1/vmlinux\n");
			fprintf(stderr, "  print 36289.1\n");
			return true;
		}

		if (c == "s" || c == "search") {
			fprintf(stderr, "Search the provenance node names (files or processes) and return the matching\n");
			fprintf(stderr, "p-node numbers.\n");
			fprintf(stderr, "\nUsage: search PATTERN\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  search */vmlinux\n");
			fprintf(stderr, "  search *.ko\n");
			return true;
		}

		if (c == "b" ||c == "best") {
			fprintf(stderr, "Print the p-nodes with the top N scores\n");
			fprintf(stderr, "\nUsage: best [NUMBER] [ALGORITHM]\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  best\n");
			fprintf(stderr, "  best 15 PageRank\n");
			return true;
		}

		if (c == "a" || c == "ancestry" || c == "ancestors") {
			fprintf(stderr, "Get the provenance graph of ancestors of the given p-node\n");
			fprintf(stderr, "\nUsage: ancestors NODE [OPTIONS...]\n");
			fprintf(stderr, "\n"); PrintOptions();
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  ancestors 36289.1 d=PR\n");
			fprintf(stderr, "  ancestors 36289.1 S=Thumb a=ProvRank o=Graphviz\n");
			return true;
		}

		if (c == "d" || c == "descendants") {
			fprintf(stderr, "Get the provenance graph of descendants of the given p-node\n");
			fprintf(stderr, "\nUsage: descendants NODE [OPTIONS...]\n");
			fprintf(stderr, "\n"); PrintOptions();
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  descendants 36289.1\n");
			fprintf(stderr, "  descendants 36289.1 a=SubRank o=Graphviz\n");
			return true;
		}

		if (c == "r" || c == "range") {
			fprintf(stderr, "Get the sizes of ancestry graphs for a range of parameter values\n");
			fprintf(stderr, "\nUsage: range NODE PARAM FROM STEP TO [OPTIONS...]\n");
			fprintf(stderr, "\n"); PrintOptions();
			fprintf(stderr, "\nSupported Parameters: cutoff, cutoff-jump, cutoff-mult, cutoff-mean\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  range 36156.2 cutoff-mult 5 1 10\n");
			fprintf(stderr, "  range 36156.2 cutoff-jump 2 0.1 5 a=ProvRank\n");
			return true;
		}

		if (c == "rd" || c == "range_desc") {
			fprintf(stderr, "Get the sizes of descendant graphs for a range of parameter values\n");
			fprintf(stderr, "\nUsage: range_desc NODE PARAM FROM STEP TO [OPTIONS...]\n");
			fprintf(stderr, "\n"); PrintOptions();
			fprintf(stderr, "\nSupported Parameters: cutoff, cutoff-jump, cutoff-mult, cutoff-mean\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  range_desc 36156.2 cutoff-mult 5 1 10\n");
			fprintf(stderr, "  range_desc 36156.2 cutoff-jump 2 0.1 5 a=ProvRank\n");
			return true;
		}

		if (c == "def" || c == "default" || c == "defaults") {
			fprintf(stderr, "Print or set the values of default parameters used by other commands\n");
			fprintf(stderr, "\nUsage: def [OPTIONS...]\n");
			fprintf(stderr, "\n"); PrintOptions();
			fprintf(stderr, "\nIf the command is called without any options, it just prints the current\n");
			fprintf(stderr, "default values.\n");
			fprintf(stderr, "\nExamples:\n");
			fprintf(stderr, "  def\n");
			fprintf(stderr, "  def a=ProvRank s=none\n");
			return true;
		}

		fprintf(stderr, "Invalid command: %s\n", c.c_str());
		return true;
	}


	// Get a PageRank

	if (cmd == "p" || cmd == "print") {
		if (args.size() != 1) {
			fprintf(stderr, "Error: Invalid number of arguments\n");
			fprintf(stderr, "Usage: print FILE_NAME|NODE\n");
			return true;
		}

		Node* n = Lookup(args[0].c_str());
		if (n == NULL) {
			fprintf(stderr, "Error: Node %s does not exit\n", args[0].c_str());
			return true;
		}

		printf("%s = %Lf\n", AlgorithmName(), Rank(n));
		return true;
	}


	// Search for a file

	if (cmd == "s" || cmd == "search") {
		if (args.size() != 1) {
			fprintf(stderr, "Error: Invalid number of arguments\n");
			fprintf(stderr, "Usage: search PATTERN\n");
			return true;
		}

		for (int ni = 0; ni < nodes.size(); ni++) {
			if (nodes[ni]->next != NULL) continue;
			if (nodes[ni]->type != "FILE" && nodes[ni]->type != "NP_FILE") continue;

			if (fnmatch(args[0].c_str(), nodes[ni]->name.c_str(), 0) == 0) {
				std::cout << NodeName(nodes[ni], true, true) << std::endl;
			}
		}

		return true;
	}


	// Get best nodes

	if (cmd == "b" || cmd == "best") {
		if (args.size() > 2) {
			fprintf(stderr, "Error: Invalid number of arguments\n");
			fprintf(stderr, "Usage: best [NUMBER] [ALGORITHM]\n");
			return true;
		}

		int alg = args.size() >= 2 ? AlgorithmID(args[1].c_str()) : defaults.algorithm;
		int num = args.size() >= 1 ? atoi(args[0].c_str()) : 10;
		if (num < 1) num = 1;

		if (alg < 0) {
			fprintf(stderr, "Error: Invalid algorithm\n");
			return true;
		}

		std::vector<Node*> n = nodes;
		BaseRank = 0;
		Sort(n, alg);

		if (num > n.size()) num = n.size();
		for (int i = 0; i < num; i++) {
			printf("%12Lf %s\n", Rank(n[i], alg), NodeName(n[i], true, true).c_str());
		}
		return true;
	}


	// Get the ancestry

	if (cmd == "a" || cmd == "ancestry" || cmd == "ancestors" || cmd == "d" || cmd == "descendants") {

		bool anc = cmd == "a" || cmd == "ancestry" || cmd == "ancestors";

		if (args.size() < 1) {
			fprintf(stderr, "Usage: %s NODE [OPTIONS...]\n", anc ? "ancestors" : "descendants");
			PrintOptions();
			return true;
		}


		// Look up the node

		Node* n = Lookup(args[0].c_str());
		if (n == NULL) {
			fprintf(stderr, "Error: Node %s does not exit\n", args[0].c_str());
			return true;
		}


		// Extract the arguments

		KeyVal K;
		Parameters P;
		if (!ExtractKeyVal(K, args, 1)) return false;
		if (!ExtractParameters(P, K)) return true;


		// Apply the rule of thumb, if configured to do so

		if (P.stop == STOP_THUMB) {

			P.cutoff_abs  = LDBL_INFINITY;
			P.cutoff_jump = LDBL_INFINITY;
			P.cutoff_mean = LDBL_INFINITY;

			if (!alg_SubGraphInputs) SubgraphSizes(true, false);

			BaseRank = 0;
			P.cutoff_mult = std::pow(1.0 / Rank(n, P.algorithm), (long double) 1.0 / std::sqrt((n->numInputs + 1) / 2.0));

			if (verbose) fprintf(stdout, "cutoff-mult = %Lf\n", P.cutoff_mult);
		}


		// Run the query

		double tstart = seconds();

		AncestryResult* r = AncestryQuery(n, anc, P.algorithm, P.cutoff_abs, P.cutoff_mult, P.cutoff_jump,
		                                  P.traversal, P.recursive, P.recursive, P.base, P.cutoff_mean, NULL);

		if (r != NULL) {

			// Postprocess the result

			if (P.summarize != SUM_NONE) r->Summarize(P.summarize == SUM_AGGRESSIVE);
			if (!P.npfiles) r->HideByType("NP_FILE");
			if ((P.display & DISP_ALL_NODES) != 0) {
				AncestryResult* all = CompleteAncestry(n, anc);
				all->SetSubset(r);
				r = all;
			}
			if ((P.display & DISP_NO_WELL_KNOWNS) != 0) r->HideStopNodes();

			double tend = seconds();

			if (verbose) {
				fprintf(stdout, "Query: %0.2lf seconds\n", tend - tstart);
			}


			// Print the result

			if (P.output == OUT_TEXT      ) r->Print(stdout, P.display);
			if (P.output == OUT_GRAPHVIZ  ) Graphviz(r, P.file.c_str(), P.format.c_str(), P.display);
			if (P.output == OUT_STATISTICS) Statistics(r);

			delete r;
		}
		else {
			fprintf(stderr, "Error: Unable to compute the ancestry");
		}

		return true;
	}


	// Explore range of a parameter

	if (cmd == "r" || cmd == "range" || cmd == "rd" || cmd == "range_desc") {

		bool anc = cmd == "r" || cmd == "range";

		if (args.size() < 5) {
			fprintf(stderr, "Usage: %s NODE PARAM FROM STEP TO [OPTIONS...]\n", anc ? "range" : "range_desc");
			fprintf(stderr, "Supported Parameters: cutoff, cutoff-jump, cutoff-mult, cutoff-mean\n");
			PrintOptions();
			return true;
		}


		// Look up the node

		Node* n = Lookup(args[0].c_str());
		if (n == NULL) {
			fprintf(stderr, "Error: Node %s does not exit\n", args[0].c_str());
			return true;
		}


		// Get the parameter

		std::string param = args[1];
		StandardizeKey(param);

		char p = '.';

		if (param == "cutoff") p = 'c';
		if (param == "cutoff-jump") p = 'j';
		if (param == "cutoff-mult") p = 'm';
		if (param == "cutoff-mean") p = 'u';

		if (p == '.') {
			fprintf(stderr, "Error: Invalid parameter \"%s\"\n", args[1].c_str());
			return true;
		}


		// Get the exploration space

		char* e = NULL;

		long double from = strtold(args[2].c_str(), &e);
		if (*e != '\0' || from < 0) {
			fprintf(stderr, "Error: Invalid parameter range\n");
			return true;
		}

		long double to = strtold(args[4].c_str(), &e);
		if (*e != '\0' || to < 0) {
			fprintf(stderr, "Error: Invalid parameter range\n");
			return true;
		}

		long double step = strtold(args[3].c_str(), &e);
		if (*e != '\0' || (from < to ? step <= 0.0001 : step >= 0.0001)) {
			fprintf(stderr, "Error: Invalid parameter step\n");
			return true;
		}


		// Extract the options

		Parameters P;
		if (!ExtractParameters(P, args, 5)) return true;


		// Check the stopping condition

		if (P.stop == STOP_THUMB) {

			if (p == 'm') {
				fprintf(stderr, "Error: Incompatible combination of the parameter and the stopping criterium\n");
				return true;
			}

			P.cutoff_abs  = LDBL_INFINITY;
			P.cutoff_jump = LDBL_INFINITY;
			P.cutoff_mean = LDBL_INFINITY;

			if (!alg_SubGraphInputs) SubgraphSizes(true, false);

			BaseRank = 0;
			P.cutoff_mult = std::pow(1.0 / Rank(n, P.algorithm), (long double) 1.0 / std::sqrt((n->numInputs + 1) / 2.0));

			if (verbose) fprintf(stdout, "cutoff-mult = %Lf\n", P.cutoff_mult);
		}


		// Get the output type

		bool out_std = P.file == "";
		std::string file = P.file;

		bool out_txt = P.format == "txt" || P.format == "dat" || P.format == "text";
		bool out_csv = P.format == "csv";
		bool out_normal = out_txt || out_csv;

		bool out_gnuplot = P.format == "gif" || P.format == "fig" || P.format == "jpg" || P.format == "pdf"
			|| P.format == "jpeg" || P.format == "svg" || P.format == "png" || P.format == "emf";
		if (P.format == "jpg") P.format = "jpeg";
		if (out_std) out_gnuplot = false;

		bool out_gnuplot_int = (P.format == "" || P.format == "svg") && (P.file == "g" || P.file == "gnuplot" || P.file == "G");
		out_gnuplot = out_gnuplot || out_gnuplot_int;

		if (out_std) {
			out_normal = false;
			out_gnuplot = true;
			out_gnuplot_int = true;
		}

		if (!out_normal && !out_gnuplot) {
			fprintf(stderr, "Error: Invalid output file type\n");
			return true;
		}


		// Open the file

		if (out_gnuplot) file = "/tmp/cs222.dat";

		FILE* f = stdout;

		if ((out_normal || out_gnuplot) && !(out_std && out_normal)) {
			f = fopen(file.c_str(), "w");
			if (f == NULL) {
				fprintf(stderr, "Error: Cannot create %s\n", file.c_str());
				return true;
			}
		}


		// Run the queries

		double tstart = seconds();
		int count = 0;

		for (long double v = from; from < to ? v <= to + 0.0001 : v >= to - 0.0001; v += step) {

			AncestryResult* r = NULL;
			count++;

			if (p == 'c') r = AncestryQuery(n, anc, P.algorithm, v           , P.cutoff_mult, P.cutoff_jump,
		                                    P.traversal, P.recursive , P.recursive  , P.base, P.cutoff_mean, NULL);
			if (p == 'm') r = AncestryQuery(n, anc, P.algorithm, P.cutoff_abs, v            , P.cutoff_jump,
		                                    P.traversal, P.recursive , P.recursive  , P.base, P.cutoff_mean, NULL);
			if (p == 'j') r = AncestryQuery(n, anc, P.algorithm, P.cutoff_abs, P.cutoff_mult, v            ,
		                                    P.traversal, P.recursive , P.recursive  , P.base, P.cutoff_mean, NULL);
			if (p == 'u') r = AncestryQuery(n, anc, P.algorithm, P.cutoff_abs, P.cutoff_mult, P.cutoff_jump,
		                                    P.traversal, P.recursive , P.recursive  , P.base, v            , NULL);

			if (r == NULL) {
				fprintf(stderr, "Error: Unable to execute the ancestry query");
				if (f != stdout && f != stderr && f != NULL) fclose(f);
				break;
			}

			if (!P.npfiles) r->HideByType("NP_FILE");
			if ((P.display & DISP_NO_WELL_KNOWNS) != 0) r->HideStopNodes();
			if (P.summarize != SUM_NONE) r->Summarize(P.summarize == SUM_AGGRESSIVE);

			fprintf(f, "%Lf%c%d\n", v, out_csv ? ',' : '\t', r->CountNodes());

			delete r;
		}

		double tend = seconds();

		if (verbose && count > 0) {
			fprintf(stdout, "%d quer%s: %0.2lf seconds (%0.2lf ms/query)\n",
					count, count == 1 ? "y" : "ies", tend - tstart,
					1000.0 * (tend - tstart) / count);
		}

		if (f != stdout && f != stderr && f != NULL) fclose(f);


		// Run gnuplot

		if (out_gnuplot) {
			std::string gfile = "/tmp/cs222.gp";

			f = fopen(gfile.c_str(), "w");
			if (f == NULL) {
				fprintf(stderr, "Error: Cannot create %s\n", gfile.c_str());
				return true;
			}

			fprintf(f, "set autoscale\n");
			fprintf(f, "unset log\n");
			fprintf(f, "unset label\n");
			fprintf(f, "set xtic auto\n");
			fprintf(f, "set ytic auto\n");
			fprintf(f, "set xlabel '%s'\n", param.c_str());
			fprintf(f, "set ylabel 'Number of Nodes'\n");
			fprintf(f, "\n");
			if (!out_gnuplot_int) {
				fprintf(f, "set terminal %s\n", P.format.c_str());
				fprintf(f, "set output '%s'\n", P.file.c_str());
			}
			else {
#ifdef _MAC
				fprintf(f, "set terminal svg\n");
				fprintf(f, "set output '/tmp/cs222.svg'\n");
#else
				fprintf(f, "set terminal gif\n");
				fprintf(f, "set output '/tmp/cs222.gif'\n");
#endif
			}
			fprintf(f, "plot '%s' using 1:2 title '' with lines lt 2\n", file.c_str());

			fclose(f);

			std::string cmd = "gnuplot ";
			cmd += gfile;
#ifdef _MAC
			cmd += " && open -a ";
			cmd += svgApp;
			cmd += " /tmp/cs222.svg";
#else
			cmd += " && (eog /tmp/cs222.gif &)";
#endif

			int r = system(cmd.c_str());
			(void) r;
		}

		return true;
	}


	// Set the defaults

	if (cmd == "def" || cmd == "default" || cmd == "defaults") {

		// Extract the arguments

		Parameters P;
		if (!ExtractParameters(P, args, 0)) return true;

		P.file = "";
		P.format = "svg";


		// Commit

		defaults = P;


		// Print

		fprintf(stdout, "Defaults:\n");
		fprintf(stdout, "  algorithm   = %s\n" , AlgorithmName(defaults.algorithm));
		fprintf(stdout, "  base        = %s\n" , defaults.base ? "yes" : "no");
		if (IS_INFINITY(defaults.cutoff_abs))
			fprintf(stdout, "  cutoff      = infinity\n");
		else
			fprintf(stdout, "  cutoff      = %Lf\n", defaults.cutoff_abs);
		if (IS_INFINITY(defaults.cutoff_jump))
			fprintf(stdout, "  cutoff-jump = infinity\n");
		else
			fprintf(stdout, "  cutoff-jump = %Lf\n", defaults.cutoff_jump);
		if (IS_INFINITY(defaults.cutoff_mean))
			fprintf(stdout, "  cutoff-mean = infinity\n");
		else
			fprintf(stdout, "  cutoff-mean = %Lf\n", defaults.cutoff_mean);
		if (IS_INFINITY(defaults.cutoff_mult))
			fprintf(stdout, "  cutoff-mult = infinity\n");
		else
			fprintf(stdout, "  cutoff-mult = %Lf\n", defaults.cutoff_mult);
		fprintf(stdout, "  display     = %s\n" , DisplayFlags(defaults.display));
		fprintf(stdout, "  npfiles     = %s\n" , defaults.npfiles ? "yes" : "no");
		fprintf(stdout, "  output      = %s\n" , OutputTypeName(defaults.output));
		fprintf(stdout, "  recursive   = %s\n" , defaults.recursive ? "yes" : "no");
		fprintf(stdout, "  stop        = %s\n" , StopTypeName(defaults.stop));
		fprintf(stdout, "  summarize   = %s\n" , SummarizeTypeName(defaults.summarize));
		fprintf(stdout, "  traversal   = %s\n" , OrderTypeName(defaults.traversal));

		return true;
	}

    // Dump the map
	if (cmd == "dump") {
        DumpCSV(args[1].c_str());
		return true;
	}

	// Error

	fprintf(stderr, "Invalid command: %s\n", cmd.c_str());
	return true;
}


/**
 * The entry point to the application
 *
 * @param argc the number of command-line arguments
 * @param argv the command-line arguments
 * @return the exit code
 */
int main(int argc, char * const argv[])
{
	int r;
	char c;
	std::vector<std::string> cmds;

	bool provRank = false;
	bool pageRank = false;
	bool  subRank = false;
	int nAlg = 0;

	std::srand(time(NULL));


	// Parse the command-line arguments

	while ((c = getopt (argc, argv, "a:c:hpvzCPRS")) != -1) {
		switch (c) {

			case 'a':
				svgApp = optarg;
				break;

			case 'c':
				cmds.push_back(std::string(optarg));
				break;

			case 'h':
				usage(argv[0]);
				return 0;

			case 'p':
				linkVersions = false;
				break;

			case 'v':
				verbose = true;
				break;

			case 'z':
				noZeroVersions = false;
				break;

			case 'C':
				collapseVersions = true;
				noZeroVersions = false;
				linkVersions = false;
				break;

			case 'P':
				provRank = true;
				defaults.algorithm = ALG_PROVRANK;
				nAlg++;
				break;

			case 'R':
				pageRank = true;
				defaults.algorithm = ALG_PAGERANK;
				nAlg++;
				break;

			case 'S':
				subRank = true;
				defaults.algorithm = ALG_SUBRANK;
				nAlg++;
				break;

			default:
				return 1;
		}
	}

	if (optind >= argc) {
		fprintf(stderr, "%s: No input files\n\n", argv[0]);
		usage(argv[0]);
		return 1;
	}

	if (nAlg == 0) {
		defaults.algorithm = ALG_PROVRANK;
	}


	// Load the files

	double tstart = seconds();

	for (int index = optind; index < argc; index++) {
		if (verbose) {
			double t = seconds();
			if (index == optind) {
				fprintf(stderr, "\rLoading: %d/%d", index - optind + 1, argc - optind);
			}
			else {
				fprintf(stderr, "\rLoading: %d/%d (%.2lf sec)     \b\b\b\b\b", index - optind + 1, argc - optind,
				                (t - tstart) * (argc - optind) / (float) (index - optind) - (t - tstart));
			}
			fflush(stderr);
		}
		r = LoadTwig(argv[index]);
		if (r != 0) return r;
	}

	FinalizeLoading();

	if (nodes.size() == 0) {
		fprintf(stderr, "\rError: The given files do not contain any provenance nodes\n");
		return 1;
	}

	if (verbose) fprintf(stderr, "\rLoading: %0.2lf seconds          \b\b\b\b\b\b\b\b\b\b\n", seconds() - tstart);


	// Run the desired algorithm

	if (pageRank) PageRank(200);
	if (provRank) ProvRank(200);
	if ( subRank) SubRank();


	// Run the program

	if (cmds.size() > 0) {

		// Run the pre-specified commands

		for (unsigned i = 0; i < cmds.size(); i++) {
			if (!command(cmds[i].c_str())) break;
		}
	}
	else {

		// Interact with the user

		char prompt[64];
		sprintf(prompt, "%c[1;34m%s%c[1;34m>%c[0;0m ", 27, "", 27, 27);

		while (1) {

			// Read the line

			char* str_line = readstr(prompt);
			if (!command(str_line)) break;
		}
	}

	return 0;
}
