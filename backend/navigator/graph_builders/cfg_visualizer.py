
import json
import os
import sys
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

CFG_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control Flow Graph - {function_name}</title>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            overflow: hidden;
        }
        
        .container {
            height: 100vh;
            display: flex;
        }
        
        /* LEFT SIDEBAR */
        .left-sidebar {
            width: 350px;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            box-shadow: 4px 0 20px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        
        .header {
            padding: 30px 20px;
            text-align: center;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .header h1 {
            color: #333;
            font-size: 1.8em;
            margin-bottom: 8px;
        }
        
        .header p {
            color: #666;
            font-size: 0.9em;
        }
        
        .controls-section {
            padding: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .control-group {
            margin-bottom: 20px;
        }
        
        .control-group:last-child {
            margin-bottom: 0;
        }
        
        label {
            display: block;
            color: #333;
            font-weight: 600;
            font-size: 0.9em;
            margin-bottom: 8px;
        }
        
        select {
            width: 100%;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            background: white;
            border: 2px solid #ddd;
            color: #333;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        select:hover {
            border-color: #667eea;
        }
        
        select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .button-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin-top: 15px;
        }
        
        button {
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        button:active {
            transform: translateY(0);
        }
        
        .stats-section {
            padding: 20px;
            border-bottom: 2px solid #f0f0f0;
        }
        
        .stats-section h3 {
            color: #333;
            font-size: 1.2em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .stat {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .stat-label {
            display: block;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.85em;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        .stat-value {
            display: block;
            color: white;
            font-size: 2em;
            font-weight: bold;
        }
        
        .legend-section {
            padding: 20px;
            flex: 1;
        }
        
        .legend-section h3 {
            color: #333;
            font-size: 1.2em;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .legend-items {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        
        .legend-item:hover {
            background: #e9ecef;
            transform: translateX(5px);
        }
        
        .legend-color {
            width: 40px;
            height: 40px;
            border-radius: 8px;
            border: 2px solid #ddd;
            flex-shrink: 0;
        }
        
        .legend-label {
            font-weight: 500;
            color: #333;
            font-size: 0.95em;
        }
        
        /* RIGHT GRAPH AREA */
        .graph-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 20px;
            overflow: hidden;
        }
        
        .graph-container {
            flex: 1;
            background: white;
            border-radius: 15px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.15);
            overflow: hidden;
            position: relative;
        }
        
        #cfg-graph {
            width: 100%;
            height: 100%;
            background: white;
        }
        
        .loading {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #666;
            font-size: 1.2em;
            text-align: center;
        }
        
        .error {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: #f44336;
            font-size: 1.2em;
            text-align: center;
            max-width: 80%;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- LEFT SIDEBAR -->
        <div class="left-sidebar">
            <div class="header">
                <h1>🔀 CFG Viewer</h1>
                <p>Control Flow Graph</p>
            </div>
            
            <div class="controls-section">
                <div class="control-group">
                    <label for="function-select">📋 Select Function</label>
                    <select id="function-select"></select>
                </div>
                
                <div class="button-group">
                    <button onclick="resetView()">🔄 Reset</button>
                    <button onclick="fitGraph()">📐 Fit</button>
                    <button onclick="exportImage()">📷 Export</button>
                    <button onclick="togglePhysics()">⚡ Physics</button>
                </div>
            </div>
            
            <div class="stats-section">
                <h3>📊 Statistics</h3>
                <div class="stats-grid">
                    <div class="stat">
                        <span class="stat-label">Nodes</span>
                        <span class="stat-value" id="total-nodes">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Edges</span>
                        <span class="stat-value" id="total-edges">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Branches</span>
                        <span class="stat-value" id="total-branches">0</span>
                    </div>
                    <div class="stat">
                        <span class="stat-label">Loops</span>
                        <span class="stat-value" id="total-loops">0</span>
                    </div>
                </div>
            </div>
            
            <div class="legend-section">
                <h3>🎨 Node Types</h3>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #4CAF50;"></div>
                        <span class="legend-label">Entry / Exit</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #2196F3;"></div>
                        <span class="legend-label">Statement</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #FF9800;"></div>
                        <span class="legend-label">Condition</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #9C27B0;"></div>
                        <span class="legend-label">Loop</span>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- RIGHT GRAPH AREA -->
        <div class="graph-area">
            <div class="graph-container">
                <div id="cfg-graph"></div>
            </div>
        </div>
    </div>

    <script>
        // Check if vis.js is loaded
        if (typeof vis === 'undefined') {
            console.error('vis.js library failed to load!');
            document.getElementById('cfg-graph').innerHTML = '<div class="error">Error: vis.js library failed to load.<br>Check your internet connection.</div>';
        } else {
            console.log('vis.js loaded successfully');
        }
        
        let cfgData = CFG_DATA_PLACEHOLDER;
        
        console.log('Initial CFG Data:', cfgData);
        
        // Handle both old and new CFG data formats
        if (cfgData.functions) {
            cfgData = cfgData.functions;
            console.log('Extracted functions:', cfgData);
        }
        
        let network = null;
        let currentFunction = null;
        let physicsEnabled = false;

        const nodeColors = {
            'entry': { color: '#4CAF50', border: '#388E3C' },
            'exit': { color: '#4CAF50', border: '#388E3C' },
            'statement': { color: '#2196F3', border: '#1976D2' },
            'condition': { color: '#FF9800', border: '#F57C00' },
            'loop': { color: '#9C27B0', border: '#7B1FA2' }
        };

        function initializeFunctionSelect() {
            console.log('Initializing function select...');
            const select = document.getElementById('function-select');
            select.innerHTML = '';
            
            const validFunctions = Object.keys(cfgData).filter(funcName => 
                cfgData[funcName].nodes && cfgData[funcName].nodes.length > 0
            );
            
            console.log('Valid functions:', validFunctions);
            
            if (validFunctions.length === 0) {
                select.innerHTML = '<option>No valid functions found</option>';
                document.getElementById('cfg-graph').innerHTML = '<div class="error">No control flow data available</div>';
                return;
            }
            
            validFunctions.forEach(funcName => {
                const option = document.createElement('option');
                option.value = funcName;
                option.textContent = funcName;
                select.appendChild(option);
            });
            
            if (validFunctions.length > 0) {
                currentFunction = validFunctions[0];
                select.value = currentFunction;
                console.log('Loading first function:', currentFunction);
                loadFunction(currentFunction);
            }
            
            select.addEventListener('change', (e) => {
                loadFunction(e.target.value);
            });
        }

        function loadFunction(funcName) {
            console.log('Loading function:', funcName);
            currentFunction = funcName;
            const cfg = cfgData[funcName];
            console.log('CFG data for function:', cfg);
            
            if (cfg && cfg.nodes && cfg.nodes.length > 0) {
                console.log('Building graph with', cfg.nodes.length, 'nodes and', cfg.edges.length, 'edges');
                buildGraph(cfg);
                updateStats(cfg);
            } else if (cfg && cfg.error) {
                document.getElementById('cfg-graph').innerHTML = '<div class="error">Error: ' + cfg.error + '</div>';
            }
        }

        function buildGraph(cfg) {
            console.log('buildGraph called with:', cfg);
            
            const nodes = cfg.nodes.map(node => ({
                id: node.id,
                label: node.label + (node.line ? `\\nLine ${node.line}` : ''),
                ...nodeColors[node.type],
                shape: node.type === 'condition' ? 'diamond' : 
                       node.type === 'loop' ? 'box' :
                       node.type === 'entry' || node.type === 'exit' ? 'ellipse' : 'box',
                font: { color: '#ffffff', size: 16, face: 'monospace', bold: true },
                margin: 15,
                borderWidth: 3
            }));
            
            console.log('Mapped nodes:', nodes);
            
            const edges = cfg.edges.map(edge => ({
                from: edge.from,
                to: edge.to,
                label: edge.label,
                arrows: { to: { enabled: true, scaleFactor: 1.5 } },
                color: edge.label === 'true' ? { color: '#4CAF50', highlight: '#66BB6A' } :
                       edge.label === 'false' ? { color: '#f44336', highlight: '#ef5350' } :
                       edge.label === 'loop' ? { color: '#9C27B0', highlight: '#BA68C8' } :
                       { color: '#666', highlight: '#999' },
                font: { size: 14, color: '#333', strokeWidth: 0, background: '#ffffff' },
                width: 3,
                smooth: { type: 'cubicBezier', roundness: 0.5 }
            }));
            
            console.log('Mapped edges:', edges);
            
            const container = document.getElementById('cfg-graph');
            console.log('Container element:', container);
            
            const data = { nodes: new vis.DataSet(nodes), edges: new vis.DataSet(edges) };
            
            const options = {
                layout: {
                    hierarchical: {
                        direction: 'UD',
                        sortMethod: 'directed',
                        nodeSpacing: 180,
                        levelSeparation: 150,
                        treeSpacing: 250
                    }
                },
                physics: {
                    enabled: false
                },
                interaction: {
                    dragNodes: true,
                    dragView: true,
                    zoomView: true,
                    hover: true
                },
                nodes: {
                    shadow: {
                        enabled: true,
                        color: 'rgba(0,0,0,0.3)',
                        size: 15,
                        x: 3,
                        y: 3
                    }
                },
                edges: {
                    shadow: {
                        enabled: true,
                        color: 'rgba(0,0,0,0.2)',
                        size: 8,
                        x: 2,
                        y: 2
                    }
                }
            };
            
            console.log('Creating vis.Network...');
            try {
                network = new vis.Network(container, data, options);
                console.log('Network created successfully');
                
                network.on('click', function(params) {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        const node = cfg.nodes.find(n => n.id === nodeId);
                        if (node) {
                            alert(`Node: ${node.label}\\nType: ${node.type}\\nLine: ${node.line || 'N/A'}`);
                        }
                    }
                });
                
                // Auto-fit after network is stable
                network.once('stabilizationIterationsDone', function() {
                    network.fit({
                        animation: {
                            duration: 1000,
                            easingFunction: 'easeInOutQuad'
                        }
                    });
                });
            } catch (error) {
                console.error('Error creating network:', error);
                document.getElementById('cfg-graph').innerHTML = '<div class="error">Error creating visualization: ' + error.message + '</div>';
            }
        }

        function updateStats(cfg) {
            document.getElementById('total-nodes').textContent = cfg.nodes.length;
            document.getElementById('total-edges').textContent = cfg.edges.length;
            
            const branches = cfg.edges.filter(e => e.label === 'true' || e.label === 'false').length / 2;
            document.getElementById('total-branches').textContent = Math.floor(branches);
            
            const loops = cfg.edges.filter(e => e.label === 'loop').length;
            document.getElementById('total-loops').textContent = loops;
        }

        function resetView() {
            if (network) {
                network.fit({
                    animation: {
                        duration: 500,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }
        }

        function fitGraph() {
            if (network) {
                network.fit();
            }
        }

        function togglePhysics() {
            if (network) {
                physicsEnabled = !physicsEnabled;
                network.setOptions({ physics: { enabled: physicsEnabled } });
            }
        }

        function exportImage() {
            alert('Export functionality coming soon!');
        }

        // Initialize on page load
        window.addEventListener('load', function() {
            console.log('Page loaded, initializing...');
            console.log('vis object:', typeof vis);
            console.log('cfg-graph element:', document.getElementById('cfg-graph'));
            initializeFunctionSelect();
        });
    </script>
</body>
</html>
"""

def generate_cfg_html(cfg_json_path, output_html_path):
    """Generate interactive HTML visualization from CFG JSON file"""
    try:
        # Read CFG JSON
        with open(cfg_json_path, 'r', encoding='utf-8') as f:
            cfg_data = json.load(f)
        
        # Get first function name for title
        if 'functions' in cfg_data and cfg_data['functions']:
            function_name = list(cfg_data['functions'].keys())[0]
        elif cfg_data:
            function_name = list(cfg_data.keys())[0]
        else:
            function_name = "Unknown"
        
        # Generate HTML by replacing placeholder
        html_content = CFG_HTML_TEMPLATE.replace('CFG_DATA_PLACEHOLDER', json.dumps(cfg_data))
        html_content = html_content.replace('{function_name}', function_name)
        
        # Write HTML file
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ CFG HTML visualization saved to {output_html_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error generating CFG HTML: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python cfg_visualizer.py <cfg_json_file> <output_html_file>")
        sys.exit(1)
    
    cfg_json_path = sys.argv[1]
    output_html_path = sys.argv[2]
    
    if not os.path.exists(cfg_json_path):
        print(f"❌ Error: CFG JSON file not found: {cfg_json_path}")
        sys.exit(1)
    
    success = generate_cfg_html(cfg_json_path, output_html_path)
    sys.exit(0 if success else 1)