const fs = require('fs');
const path = require('path');
const folder = 'C:\\Users\\sbokk\\OneDrive\\Desktop\\GITHUB REPOS\\Core-algorithms-for-Leetcode';
const files = ['09_Graph_DFS_BFS.ipynb','10_Topological_Sort.ipynb','11_Top_K_Elements.ipynb','12_Subsets_Backtracking.ipynb'];
for (const f of files) {
  const nb = JSON.parse(fs.readFileSync(path.join(folder, f), 'utf8'));
  const samples = nb.cells.filter(c => c.cell_type === 'markdown' && c.source && c.source.length > 0).slice(0,6).map(c => JSON.stringify(c.source[0]));
  console.log('\n--- ' + f + ' ---');
  samples.forEach(s => console.log(s));
}
