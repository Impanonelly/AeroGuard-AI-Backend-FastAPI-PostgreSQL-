const fs = require('fs');
const path = require('path');

const frontendDir = path.resolve('../aeroguard_frontend/src');

function tryRename(from, to) {
  const fromPath = path.join(frontendDir, from);
  const toPath = path.join(frontendDir, to);
  if (fs.existsSync(fromPath)) {
    console.log(`Renaming ${from} to ${to}`);
    fs.renameSync(fromPath, toPath);
  }
}

tryRename('components/AppLayout.jsx', 'pages/Root.jsx');
tryRename('pages/AlcoholScreening.jsx', 'pages/AlcoholSubstance.jsx');
tryRename('pages/DutyManagement.jsx', 'pages/FlightDutyManagement.jsx');

const placeholders = ['AlertnessFatigue.jsx', 'ComplianceManagement.jsx', 'NotificationCenter.jsx'];
placeholders.forEach(file => {
  const name = file.replace('.jsx', '');
  const filePath = path.join(frontendDir, 'pages', file);
  if (!fs.existsSync(filePath)) {
    console.log(`Creating placeholder ${file}`);
    const content = `import React from 'react';
export function ${name}() {
  return (
    <div style={{ display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', minHeight:'60vh', gap:16 }}>
      <h1 className="text-3xl font-bold">${name.replace(/([A-Z])/g, ' $1').trim()}</h1>
      <p style={{ color:'var(--gray-600)' }}>This module is coming soon.</p>
    </div>
  );
}`;
    fs.writeFileSync(filePath, content);
  }
});

function updateExportsInDir(dirPath) {
  const files = fs.readdirSync(dirPath);
  for (const file of files) {
    const filePath = path.join(dirPath, file);
    const stat = fs.statSync(filePath);
    if (stat.isDirectory()) {
      updateExportsInDir(filePath);
    } else if (file.endsWith('.jsx')) {
      let content = fs.readFileSync(filePath, 'utf8');
      
      // Update function names
      if (file === 'Root.jsx') {
        content = content.replace(/function AppLayout/g, 'function Root');
        content = content.replace(/from '\.\/Sidebar'/g, "from '../components/Sidebar'");
      }
      if (file === 'AlcoholSubstance.jsx') {
        content = content.replace(/function AlcoholScreening/g, 'function AlcoholSubstance');
      }
      if (file === 'FlightDutyManagement.jsx') {
        content = content.replace(/function DutyManagement/g, 'function FlightDutyManagement');
      }
      
      // Change export default function Name to export function Name
      content = content.replace(/export default function\s+([A-Za-z0-9_]+)/g, 'export function $1');
      
      fs.writeFileSync(filePath, content);
    }
  }
}

console.log("Updating exports...");
updateExportsInDir(path.join(frontendDir, 'pages'));
updateExportsInDir(path.join(frontendDir, 'components'));
console.log("Migration complete.");
