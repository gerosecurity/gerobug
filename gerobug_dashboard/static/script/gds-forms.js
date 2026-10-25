/* Gero design system — shared AJAX submit helper.
 *
 * Every AJAX form/button handler funnels through gdsSubmit so server-side
 * outcomes are always surfaced to the operator:
 *   - default success path reloads the page, so Django messages (both
 *     success messages AND form.errors converted to messages) render —
 *     the systematic fix for AJAX submits silently swallowing errors;
 *   - failures render an inline dismissable banner with the server's
 *     JSON error when present (no blocking alert() dialogs).
 */
(function ($) {
  'use strict';

  function banner(msg, level) {
    var host = document.querySelector('.home-section main') || document.body;
    var p = document.createElement('p');
    p.className = 'alert ' + (level === 'success' ? 'alert-success' : 'alert-warning');
    p.setAttribute('role', 'alert');
    var strong = document.createElement('span');
    strong.style.fontWeight = 'bold';
    strong.textContent = msg;
    p.appendChild(strong);
    host.insertBefore(p, host.firstChild);
    p.scrollIntoView({ block: 'nearest' });
    window.setTimeout(function () { p.remove(); }, 6000);
  }

  function failMessage(xhr) {
    try {
      var data = JSON.parse(xhr.responseText);
      if (data.error) { return data.error; }
      if (data.message) { return data.message; }
    } catch (e) { /* body was not JSON */ }
    if (xhr.status === 0) { return 'Could not reach the server — nothing was saved.'; }
    if (xhr.status === 403) { return 'Not allowed — are you still signed in?'; }
    return 'Request failed (HTTP ' + xhr.status + ') — nothing was saved.';
  }

  window.gdsNotify = banner;

  window.gdsSubmit = function (opts) {
    var ajax = { type: opts.type || 'POST', url: opts.url, data: opts.data };
    if (opts.formData) {
      ajax.data = opts.formData;
      ajax.processData = false;
      ajax.contentType = false;
    }
    return $.ajax(ajax)
      .done(function (response) {
        if (opts.onSuccess) { opts.onSuccess(response); return; }
        window.location.reload();
      })
      .fail(function (xhr) {
        if (opts.onError) { opts.onError(xhr); }
        banner(failMessage(xhr), 'warning');
      });
  };
})(jQuery);
