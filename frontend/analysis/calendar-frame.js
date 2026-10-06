'use strict';
// Cross-origin contents are intentionally neither read nor parsed.
(() => {
 const frame=document.getElementById('investing-calendar');
 const error=document.getElementById('calendar-frame-error');
 frame.addEventListener('error',()=>{error.hidden=false;});
})();
