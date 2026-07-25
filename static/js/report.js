// MindSense-AI Report Script

document.addEventListener('DOMContentLoaded', () => {
    // Add print media styles if needed
    const style = document.createElement('style');
    style.innerHTML = `
        @media print {
            .no-print, nav, footer { display: none !important; }
            body { background: white !important; color: black !important; }
            #printable-report { border: none !important; background: white !important; color: black !important; box-shadow: none !important; }
            .bg-slate-900, .bg-slate-950, .bg-slate-950\\/60, .bg-slate-950\\/40 { background: #f8fafc !important; border-color: #cbd5e1 !important; color: #0f172a !important; }
            .text-white, .text-slate-200, .text-slate-300 { color: #0f172a !important; }
            .text-slate-400, .text-slate-500 { color: #475569 !important; }
        }
    `;
    document.head.appendChild(style);
});
