const { app, BrowserWindow } = require('electron');
const path = require('path');

function createWindow () {
  const win = new BrowserWindow({
    width: 420,
    height: 740,
    resizable: false,
    alwaysOnTop: true, // Always on Top function requested by user
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    }
  });

  // Load the local static React files built inside /dist
  win.loadFile(path.join(__dirname, 'dist/index.html'));
  
  // Clean default top panel menus
  win.setMenu(null);
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
