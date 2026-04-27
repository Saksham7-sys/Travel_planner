#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>
#include <limits.h>
#include <cstring>
#include <cerrno>
#include <stdexcept>

using namespace std;

// ===========================================================================
// Class: CSVParser
// Responsible for reading/writing CSV files
// ===========================================================================
class CSVParser
{
public:
    // Trim whitespace and BOM from a string
    static string trim(const string& s)
    {
        size_t start = s.find_first_not_of(" \t\r\n\xEF\xBB\xBF");
        if (start == string::npos) return "";
        size_t end = s.find_last_not_of(" \t\r\n");
        return s.substr(start, end - start + 1);
    }

    // Split a CSV line respecting quoted fields
    static vector<string> splitLine(const string& line)
    {
        vector<string> fields;
        string field;
        bool inQuotes = false;

        for (size_t i = 0; i < line.size(); ++i)
        {
            char c = line[i];
            if (c == '"')                   { inQuotes = !inQuotes; }
            else if (c == ',' && !inQuotes) { fields.push_back(trim(field)); field.clear(); }
            else                            { field += c; }
        }
        fields.push_back(trim(field));
        return fields;
    }
};

// ===========================================================================
// Class: Graph
// Holds node names and the adjacency matrix; responsible for loading from CSV
// ===========================================================================
class Graph
{
public:
    static const int INF = 10000;   // sentinel for "no direct road"

    int                     N;      // number of nodes
    vector<string>          names;  // node names
    vector<vector<int>>     adj;    // adjacency matrix

    Graph() : N(0) {}

    // Load from a labeled-adjacency-matrix CSV:
    //   ,NodeA,NodeB,NodeC
    //   NodeA,0,14,9
    //   NodeB,14,0,10000
    //   NodeC,9,10000,0
    void loadFromCSV(const string& filename)
    {
        ifstream fin(filename);
        if (!fin.is_open())
            throw runtime_error("Cannot open \"" + filename + "\".");

        string line;

        // Header row -> node names
        if (!getline(fin, line))
            throw runtime_error("Input file is empty.");

        vector<string> header = CSVParser::splitLine(line);
        for (size_t i = 1; i < header.size(); ++i)
            names.push_back(header[i]);

        N = (int)names.size();
        if (N < 2)
            throw runtime_error("Need at least 2 nodes.");

        // Data rows
        adj.assign(N, vector<int>(N, INF));

        int row = 0;
        while (getline(fin, line) && row < N)
        {
            if (CSVParser::trim(line).empty()) continue;
            vector<string> cells = CSVParser::splitLine(line);

            for (int col = 0; col < N && (col + 1) < (int)cells.size(); ++col)
            {
                try   { adj[row][col] = stoi(cells[col + 1]); }
                catch (...) { adj[row][col] = INF; }
            }
            ++row;
        }

        if (row != N)
            throw runtime_error("Expected " + to_string(N) +
                                " data rows, found " + to_string(row) + ".");
    }

    // Smallest outgoing edge weight from node i (excluding self-loop)
    int firstMin(int i) const
    {
        int mn = INT_MAX;
        for (int k = 0; k < N; ++k)
            if (adj[i][k] < mn && i != k) mn = adj[i][k];
        return mn;
    }

    // Second-smallest outgoing edge weight from node i
    int secondMin(int i) const
    {
        int first = INT_MAX, second = INT_MAX;
        for (int j = 0; j < N; ++j)
        {
            if (i == j) continue;
            if (adj[i][j] <= first)
            {
                second = first;
                first  = adj[i][j];
            }
            else if (adj[i][j] < second)
            {
                second = adj[i][j];
            }
        }
        return second;
    }
};

// ===========================================================================
// Class: TSPResult
// Plain data container for the solver's output
// ===========================================================================
struct TSPResult
{
    vector<int> path;       // node indices, length N+1 (closes the tour)
    int         distance;   // total tour distance

    TSPResult() : distance(INT_MAX) {}

    bool isValid() const { return distance != INT_MAX; }
};

// ===========================================================================
// Class: TSPSolver
// Branch-and-Bound Travelling Salesman solver
// ===========================================================================
class TSPSolver
{
public:
    explicit TSPSolver(const Graph& g) : graph(g) {}

    // Run the solver and return the best result found
    TSPResult solve()
    {
        result = TSPResult();   // reset

        int n = graph.N;
        vector<int> currPath(n + 1, -1);
        visited.assign(n, false);

        // Initial lower bound: sum of (firstMin + secondMin) / 2 for all nodes
        int currBound = 0;
        for (int i = 0; i < n; ++i)
            currBound += graph.firstMin(i) + graph.secondMin(i);
        currBound = (currBound & 1) ? currBound / 2 + 1 : currBound / 2;

        visited[0]   = true;
        currPath[0]  = 0;

        tspRec(currBound, 0, 1, currPath);

        return result;
    }

private:
    const Graph& graph;
    TSPResult    result;
    vector<bool> visited;

    // Save current path as the best solution found so far
    void recordSolution(const vector<int>& currPath, int totalDist)
    {
        result.path.assign(currPath.begin(), currPath.begin() + graph.N);
        result.path.push_back(currPath[0]);   // close tour
        result.distance = totalDist;
    }

    // Recursive branch-and-bound exploration
    void tspRec(int currBound, int currWeight, int level, vector<int>& currPath)
    {
        int n = graph.N;

        if (level == n)
        {
            int back = graph.adj[currPath[level - 1]][currPath[0]];
            if (back < Graph::INF)
            {
                int total = currWeight + back;
                if (total < result.distance)
                    recordSolution(currPath, total);
            }
            return;
        }

        for (int i = 0; i < n; ++i)
        {
            int edge = graph.adj[currPath[level - 1]][i];
            if (edge >= Graph::INF || visited[i]) continue;

            int savedBound  = currBound;
            int newWeight   = currWeight + edge;

            // Tighten the lower bound
            currBound -= (level == 1)
                ? (graph.firstMin(currPath[level - 1]) + graph.firstMin(i)) / 2
                : (graph.secondMin(currPath[level - 1]) + graph.firstMin(i)) / 2;

            if (currBound + newWeight < result.distance)
            {
                currPath[level] = i;
                visited[i] = true;
                tspRec(currBound, newWeight, level + 1, currPath);
            }

            // Restore state
            currBound = savedBound;
            visited.assign(n, false);
            for (int jj = 0; jj <= level - 1; ++jj)
                visited[currPath[jj]] = true;
        }
    }
};

// ===========================================================================
// Class: ResultWriter
// Writes the TSP result to an output CSV
// ===========================================================================
class ResultWriter
{
public:
    // Write output CSV with columns: Step, District, Cumulative Distance (km)
    static void writeCSV(const string& filename,
                         const Graph&     graph,
                         const TSPResult& result)
    {
        ofstream fout(filename);
        if (!fout.is_open())
            throw runtime_error(string("Cannot open \"") + filename +
                                "\" for writing: " + strerror(errno));

        fout << "Step,District,Cumulative Distance (km)\n";

        int cumulative = 0;
        int n = graph.N;
        for (int i = 0; i <= n; ++i)
        {
            int node = result.path[i];
            if (i > 0)
            {
                int prev = result.path[i - 1];
                cumulative += graph.adj[prev][node];
            }
            fout << (i + 1) << ",\"" << graph.names[node] << "\"," << cumulative << "\n";
        }
        fout << "TOTAL,,\"" << result.distance << " km\"\n";
    }
};

// ===========================================================================
// Class: TSPApplication
// Orchestrates the full pipeline: load → solve → report → write
// ===========================================================================
class TSPApplication
{
public:
    TSPApplication(const string& inputFile, const string& outputFile)
        : inputFile(inputFile), outputFile(outputFile) {}

    int run()
    {
        cout << "Reading input from  : " << inputFile  << "\n";
        cout << "Writing output to   : " << outputFile << "\n\n";

        // 1. Load graph
        Graph graph;
        try { graph.loadFromCSV(inputFile); }
        catch (const exception& e) { cerr << "ERROR: " << e.what() << "\n"; return 1; }

        cout << "Nodes loaded (" << graph.N << "):\n";
        for (int i = 0; i < graph.N; ++i)
            cout << "  " << i << ". " << graph.names[i] << "\n";

        // 2. Solve
        cout << "\nRunning Branch-and-Bound TSP...\n";
        TSPSolver solver(graph);
        TSPResult result = solver.solve();

        if (!result.isValid())
        {
            cerr << "ERROR: No valid Hamiltonian tour found. "
                    "Check that your graph is fully connected.\n";
            return 1;
        }

        // 3. Print summary
        cout << "Done. Minimum distance: " << result.distance << " km\n";
        cout << "Path: ";
        for (int i = 0; i <= graph.N; ++i)
            cout << graph.names[result.path[i]] << (i < graph.N ? " -> " : "\n");

        // 4. Write CSV
        try { ResultWriter::writeCSV(outputFile, graph, result); }
        catch (const exception& e) { cerr << "ERROR: " << e.what() << "\n"; return 1; }

        cout << "Results written to \"" << outputFile << "\".\n";
        return 0;
    }

private:
    string inputFile;
    string outputFile;
};

// ===========================================================================
// main – unchanged interface: ./tsp_csv [input.csv [output.csv]]
// ===========================================================================
int main(int argc, char* argv[])
{
    string inputFile  = "input.csv";
    string outputFile = "output.csv";

    if (argc >= 2) inputFile  = argv[1];
    if (argc >= 3) outputFile = argv[2];

    TSPApplication app(inputFile, outputFile);
    return app.run();
}
