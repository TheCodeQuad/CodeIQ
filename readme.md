⚙️ Setup Instructions
1️⃣ Clone the Repository
git clone https://github.com/TheCodeQuad/CodeIQ.git
cd CodeIQ

2️⃣ Install Python and Dependencies
Ensure you have Python 3.9+ installed. Then install all dependencies:
pip install -r requirements.txt
If you don't have a requirements.txt, create one with:
pip install networkx matplotlib tree_sitter
pip freeze > requirements.txt
Required Python Libraries:

networkx — Graph construction and manipulation
matplotlib — Visualization and graph rendering
tree_sitter — Syntax parsing for multiple languages
json — Data serialization
os — File system operations


3️⃣ Install a C++ Compiler (Required for Tree-sitter)
Tree-sitter compiles grammars for multiple programming languages, so a C++ compiler is mandatory.
🪟 Windows (Recommended: Microsoft C++ Build Tools)

Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/
Download Build Tools for Visual Studio
During installation, select "Desktop development with C++" workload
Ensure the following components are checked:

MSVC v143 - VS 2022 C++ x64/x86 build tools
Windows 10 SDK (latest version)
C++ CMake tools for Windows
C++ ATL and MFC libraries (optional)


Wait for installation (around 3-5 GB)
Restart terminal and verify:

cl
Expected output: Microsoft (R) C/C++ Optimizing Compiler Version 19.x

🐧 Linux
sudo apt update
sudo apt install build-essential
g++ --version

🍎 macOS
xcode-select --install

4️⃣ Install Tree-sitter CLI and Language Parsers
Tree-sitter is used to parse and build syntax trees.
Step 1: Install Tree-sitter CLI globally
npm install -g tree-sitter-cli
Verify installation:
tree-sitter --version
Step 2: Install grammar repositories
Clone the grammars you plan to analyze:
git clone https://github.com/tree-sitter/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-javascript
git clone https://github.com/tree-sitter/tree-sitter-cpp
git clone https://github.com/tree-sitter/tree-sitter-java

5️⃣ Add Source Files
Place your .py, .js, .cpp, or .java files inside the source_files/ folder:
source_files/
├── test1.py
├── utils.cpp
└── script.js

6️⃣ Generate Intermediate Representation (IR)
python ir_builder.py
This script parses all files inside source_files/ and produces ir_output.json.
Example ir_output.json structure:
[
{
"file_name": "test1.py",
"functions": [
{"name": "add", "body": "return a + b"}
]
}
]

7️⃣ Build the Global CFG
python cfg.py
This creates a Global Control Flow Graph (CFG) and saves:
./global_cfg/global_cfg.png
./global_cfg/global_cfg.graphml
Expected output:
✅ Global CFG created with 142 nodes and 155 edges
🧩 Saved CFG visualization → ./global_cfg/global_cfg.png

8️⃣ Build the Global PDG
python pdg.py
This generates the Global Program Dependence Graph (PDG):
./global_pdg/global_pdg.png
./global_pdg/global_pdg.graphml

9️⃣ Visualize the Graphs
You can:

Open .png files directly to view the graph
Import .graphml files into Gephi, yEd, or Cytoscape for richer visualization


📊 Example Outputs
Graph TypeDescriptionOutput FileIRExtracted syntax informationir_output.jsonCFGControl flow structureglobal_cfg/global_cfg.pngPDGData and control dependenciesglobal_pdg/global_pdg.png

🧰 Tech Stack
ComponentTechnologyParserTree-sitterGraph RepresentationNetworkXVisualizationMatplotlibSupported LanguagesPython, JavaScript, C++, JavaOutput FormatsPNG, GraphML, JSON