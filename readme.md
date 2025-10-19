## ⚙️ Setup Instructions

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/TheCodeQuad/CodeIQ.git
cd CodeIQ
2️⃣ Install Python and Dependencies
Ensure you have Python 3.9+ installed.
Then install all dependencies:

bash
Copy code
pip install networkx matplotlib tree_sitter
pip freeze > requirements.txt
Required Python Libraries:

Library	Purpose
networkx	Graph construction and manipulation
matplotlib	Visualization and graph rendering
tree_sitter	Syntax parsing for multiple languages
json	Data serialization
os	File system operations

3️⃣ Install a C++ Compiler (Required for Tree-sitter)
Tree-sitter compiles grammars for multiple programming languages, so a C++ compiler is mandatory.

🪟 Windows (Recommended: Microsoft C++ Build Tools)
Go to: https://visualstudio.microsoft.com/visual-cpp-build-tools/

Download Build Tools for Visual Studio.

During installation:

Select "Desktop development with C++" workload.

Ensure the following components are checked:

✅ MSVC v143 - VS 2022 C++ x64/x86 build tools

✅ Windows 10 SDK (latest version)

✅ C++ CMake tools for Windows

✅ C++ ATL and MFC libraries (optional but recommended)

Wait for installation to complete (it’s around 3–5 GB).

Once done, restart your terminal and verify installation:

bash
Copy code
cl
If you see something like:

mathematica
Copy code
Microsoft (R) C/C++ Optimizing Compiler Version 19.x.xxxxx
✅ You’re good to go!

🐧 Linux
bash
Copy code
sudo apt update
sudo apt install build-essential
g++ --version
🍎 macOS
bash
Copy code
xcode-select --install
4️⃣ Install Tree-sitter CLI and Language Parsers
Tree-sitter is used to parse and build syntax trees.

Step 1: Install Tree-sitter CLI globally
bash
Copy code
npm install -g tree-sitter-cli
Verify installation:

bash
Copy code
tree-sitter --version
Step 2: Install grammar repositories
Clone the grammars you plan to analyze:

bash
Copy code
git clone https://github.com/tree-sitter/tree-sitter-python
git clone https://github.com/tree-sitter/tree-sitter-javascript
git clone https://github.com/tree-sitter/tree-sitter-cpp
git clone https://github.com/tree-sitter/tree-sitter-java
These contain the grammar definitions used by your ir_builder.py script.

5️⃣ Add Source Files
Place your .py, .js, .cpp, or .java files inside the source_files/ folder:

Copy code
source_files/
├── test1.py
├── utils.cpp
└── script.js
6️⃣ Generate Intermediate Representation (IR)
Run:

bash
Copy code
python ir_builder.py
This script parses all files inside source_files/ and produces ir_output.json.

Example structure:

json
Copy code
[
  {
    "file_name": "test1.py",
    "functions": [
      {"name": "add", "body": "return a + b"}
    ]
  }
]
7️⃣ Build the Global CFG
Run:

bash
Copy code
python cfg.py
This creates a Global Control Flow Graph (CFG) and saves:

bash
Copy code
./global_cfg/global_cfg.png
./global_cfg/global_cfg.graphml
Example output:

objectivec
Copy code
✅ Global CFG created with 142 nodes and 155 edges
🧩 Saved CFG visualization → ./global_cfg/global_cfg.png
8️⃣ Build the Global PDG
Run:

bash
Copy code
python pdg.py
This generates the Global Program Dependence Graph (PDG):

bash
Copy code
./global_pdg/global_pdg.png
./global_pdg/global_pdg.graphml
9️⃣ Visualize the Graphs
You can:

🖼️ Open .png files directly to view the graph

🌐 Import .graphml files into Gephi, yEd, or Cytoscape for richer visualization

