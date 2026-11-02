"use strict";

const { app, BrowserWindow } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

app.whenReady().then(async () => {
  const window = new BrowserWindow({ width: 1440, height: 1000, show: false, webPreferences: { sandbox: true, contextIsolation: true, nodeIntegration: false } });
  try {
    window.webContents.on("console-message", (_event, level, message) => console.log(`renderer:${level}:${message}`));
    await window.loadFile(path.join(root, "ORELYN.html"));
    await sleep(700);
    const initial = await window.webContents.executeJavaScript(`(() => ({rows:document.querySelectorAll('#source-rows tr').length,broken:[...document.images].filter(i=>i.complete&&i.naturalWidth===0).length,overflow:document.documentElement.scrollWidth>innerWidth}))()`);
    if (initial.rows !== 8 || initial.broken || initial.overflow) throw new Error(`Initial UI failed: ${JSON.stringify(initial)}`);
    await window.webContents.executeJavaScript(`(() => {const filter=document.querySelector('#license-filter');filter.value='review';filter.dispatchEvent(new Event('input',{bubbles:true}));})()`);
    const reviewRows = await window.webContents.executeJavaScript(`document.querySelectorAll('#source-rows tr').length`);
    if (reviewRows !== 1) throw new Error(`License filter failed: ${reviewRows}`);
    await window.webContents.executeJavaScript(`document.querySelector('#clear-filters').click()`);
    await window.webContents.executeJavaScript(`document.querySelector('#source-rows .detail-button').click()`);
    const dialog = await window.webContents.executeJavaScript(`(() => ({open:document.querySelector('#source-dialog').open,text:document.querySelector('#dialog-content').textContent}))()`);
    if (!dialog.open || !dialog.text.includes("CC BY")) throw new Error('Source detail dialog failed');
    await window.webContents.executeJavaScript(`document.querySelector('#close-dialog').click()`);
    await window.webContents.executeJavaScript(`(() => {const select=document.querySelector('#language-select');select.value='zh-CN';select.dispatchEvent(new Event('change',{bubbles:true}));})()`);
    const language = await window.webContents.executeJavaScript(`document.documentElement.lang`);
    if (language !== "zh-CN") throw new Error('Language switch failed');
    let image = await window.webContents.capturePage();
    fs.writeFileSync(path.join(root, "orelyn-desktop.png"), image.toPNG());
    await window.setContentSize(390, 844);
    await sleep(200);
    const mobileOverflow = await window.webContents.executeJavaScript(`document.documentElement.scrollWidth>innerWidth`);
    if (mobileOverflow) throw new Error('Mobile horizontal overflow');
    image = await window.webContents.capturePage();
    fs.writeFileSync(path.join(root, "orelyn-mobile.png"), image.toPNG());
    console.log(JSON.stringify({initial,reviewRows,dialogOpen:dialog.open,language,mobileOverflow},null,2));
    window.destroy();
    app.quit();
  } catch (error) { console.error(error); app.exit(1); }
});
