// background.js — recibe mensajes de content scripts y los envía al native host

const HOST_NAME = 'com.animeautoplay.host';

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  // Aceptar AUTO_CLICK, PRESS_F, CLICK_CENTER y cualquier mensaje para el host
  if (!msg.type || !['AUTO_CLICK', 'PRESS_F', 'CLICK_CENTER'].includes(msg.type)) return;

  chrome.runtime.sendNativeMessage(HOST_NAME, msg, (response) => {
    if (chrome.runtime.lastError) {
      console.warn('[AAP Host] Native message error:', chrome.runtime.lastError.message);
    }
    sendResponse(response ?? { ok: false });
  });

  return true; // async
});
