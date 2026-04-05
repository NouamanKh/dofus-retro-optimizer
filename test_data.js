const items = require('./data/items_retro.js');
const sets = require('./data/sets_retro.js');

console.log('Items loaded:', items.length);
console.log('First item:', JSON.stringify(items[0], null, 2));
console.log('Items with sets:', items.filter(i => i.set).length);
console.log('Items by type:', items.reduce((acc, i) => { 
    acc[i.type] = (acc[i.type] || 0) + 1; 
    return acc; 
}, {}));
console.log('Sample set item:', items.find(i => i.set));
console.log('Sets loaded:', sets.length);
console.log('First set:', JSON.stringify(sets[0], null, 2));
