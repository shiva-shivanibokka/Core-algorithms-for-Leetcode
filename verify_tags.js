const fs = require('fs');
const path = require('path');
const folder = 'C:\\Users\\sbokk\\OneDrive\\Desktop\\GITHUB REPOS\\Core-algorithms-for-Leetcode';

const files = fs.readdirSync(folder).filter(f => f.endsWith('.ipynb')).sort();

let grandTotal = 0;
for (const file of files) {
  const nb = JSON.parse(fs.readFileSync(path.join(folder, file), 'utf8'));
  const tagged = nb.cells.filter(c => c.cell_type === 'markdown' && c.source && c.source.some(s => s.includes('🏢')));
  grandTotal += tagged.length;
  // Show first tagged cell's first two source lines as a sample
  const sample = tagged[0] ? tagged[0].source.slice(0, 2).map(s => s.replace(/\n/g, '\\n')) : [];
  console.log(`${file}: ${tagged.length} tagged cells  |  sample: ${sample.join(' | ')}`);
}
console.log(`\nGrand total tagged cells: ${grandTotal}`);
