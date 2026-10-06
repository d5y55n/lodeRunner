'use strict';
const SymbolModel={
 filter(rows,query,favorites=[]){const q=query.trim().toUpperCase();return rows.filter(r=>r.symbol.includes(q)||r.base_asset.toUpperCase().includes(q)).sort((a,b)=>Number(favorites.includes(b.symbol))-Number(favorites.includes(a.symbol))||a.symbol.localeCompare(b.symbol)).slice(0,40);},
 recent(rows,symbol){return [symbol,...rows.filter(x=>x!==symbol)].slice(0,6);},
 money(value){if(value==null)return '-';return '$'+Number(value).toLocaleString('en-US',{maximumSignificantDigits:9});}
};
if(typeof module!=='undefined')module.exports=SymbolModel;
else globalThis.SymbolModel=SymbolModel;
