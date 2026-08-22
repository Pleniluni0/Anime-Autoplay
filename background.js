// background.js — Anime AutoPlay (Store version)
// Sin native messaging. El service worker queda como placeholder para
// futura compatibilidad con el host nativo instalado externamente.
// De momento solo registra que está activo.

console.log('[AAP] Background service worker loaded (Store version)');

// Si el usuario instala el host nativo por separado (desde GitHub),
// este listener se activará. Mientras tanto, rechaza silenciosamente.
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (!msg || !msg.type) return false;

  // Mensajes que van al host nativo — si no está instalado, fallan silenciosamente
  if (['AUTO_CLICK', 'PRESS_F', 'CLICK_CENTER'].includes(msg.type)) {
    try {
      chrome.runtime.sendNativeMessage('com.animeautoplay.host', msg, (response) => {
        if (chrome.runtime.lastError) {
          // Host no instalado — es normal, respuesta silenciosa
          sendResponse({ ok: false, error: 'host_not_installed' });
        } else {
          sendResponse(response ?? { ok: false });
        }
      });
    } catch (_) {
      sendResponse({ ok: false, error: 'host_not_available' });
    }
    return true; // async
  }

  return false;
});
