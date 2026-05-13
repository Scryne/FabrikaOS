/**
 * FDYS — İş Emri Kanban Board
 * Kategori 6 — İş Akışı Otomasyonu
 *
 * HTML5 Drag & Drop API ile Kanban sürükle-bırak işlevselliği.
 * AJAX ile backend durum güncellemesi.
 */

(function () {
    'use strict';

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
    let draggedCard = null;

    function initKanban() {
        const cards = document.querySelectorAll('.ie-kanban-card[draggable="true"]');
        const dropZones = document.querySelectorAll('.ie-kanban-cards');

        cards.forEach(card => {
            card.addEventListener('dragstart', handleDragStart);
            card.addEventListener('dragend', handleDragEnd);
        });

        dropZones.forEach(zone => {
            zone.addEventListener('dragover', handleDragOver);
            zone.addEventListener('dragenter', handleDragEnter);
            zone.addEventListener('dragleave', handleDragLeave);
            zone.addEventListener('drop', handleDrop);
        });
    }

    function handleDragStart(e) {
        draggedCard = this;
        this.classList.add('ie-kanban-card-dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/plain', this.dataset.id);
    }

    function handleDragEnd() {
        this.classList.remove('ie-kanban-card-dragging');
        document.querySelectorAll('.ie-kanban-cards').forEach(z => {
            z.classList.remove('ie-kanban-drop-active');
        });
        draggedCard = null;
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    function handleDragEnter(e) {
        e.preventDefault();
        this.classList.add('ie-kanban-drop-active');
    }

    function handleDragLeave() {
        this.classList.remove('ie-kanban-drop-active');
    }

    function handleDrop(e) {
        e.preventDefault();
        this.classList.remove('ie-kanban-drop-active');

        if (!draggedCard) return;

        const isEmriId = e.dataTransfer.getData('text/plain');
        const yeniDurum = this.dataset.durum;

        // DOM'da taşı
        this.appendChild(draggedCard);

        // Backend'e AJAX ile gönder
        updateStatus(isEmriId, yeniDurum);
    }

    function updateStatus(isEmriId, durum) {
        fetch('/is-emri/api/durum-guncelle', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                is_emri_id: isEmriId,
                durum: durum
            })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(data.message, 'success');
            } else {
                showToast(data.message || 'Güncelleme başarısız.', 'danger');
                // Hata durumunda sayfayı yenile
                setTimeout(() => location.reload(), 1500);
            }
        })
        .catch(() => {
            showToast('Bağlantı hatası.', 'danger');
            setTimeout(() => location.reload(), 1500);
        });
    }

    function showToast(message, type) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const bgClass = type === 'success' ? 'bg-success' : 'bg-danger';
        const toast = document.createElement('div');
        toast.className = `toast show align-items-center text-white ${bgClass} border-0 mb-2`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    // Init on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initKanban);
    } else {
        initKanban();
    }
})();
