// ==UserScript==
// @name         起点中文网导出TXT
// @namespace    http://scripts.vlper.top/
// @version      1.2
// @description  在起点章节页面添加导出按钮，支持自动导出
// @match        https://www.qidian.com/chapter/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const STORAGE_KEY = 'qidian_auto_export';
    const API_BASE = 'http://127.0.0.1:2314';

    // 状态管理
    let isAutoRunning = false;
    let exportedCount = 0;
    let bookName = '';

    // 加载状态
    function loadState() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                isAutoRunning = parsed.isAutoRunning || false;
                exportedCount = parsed.exportedCount || 0;
                bookName = parsed.bookName || '';
                return true;
            } catch (e) {
                console.error('解析保存状态失败:', e);
            }
        }
        return false;
    }

    // 保存状态
    function saveState() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({
            isAutoRunning,
            exportedCount,
            bookName
        }));
    }

    // 从页面获取章节信息
    function getChapterInfo() {
        const scriptEl = document.getElementById('vite-plugin-ssr_pageContext');
        if (!scriptEl) return null;

        try {
            const pageContext = JSON.parse(scriptEl.textContent);
            const chapterInfo = pageContext?.pageContext?.pageProps?.pageData?.chapterInfo;
            if (!chapterInfo) return null;

            const bookInfo = pageContext?.pageContext?.pageProps?.pageData?.bookInfo;

            const div = document.createElement('div');
            div.innerHTML = chapterInfo.content || '';
            const paragraphs = Array.from(div.querySelectorAll('p'))
                .map((paragraph) => paragraph.textContent.trim())
                .filter(Boolean);
            const content = paragraphs.length > 0
                ? paragraphs.join('\n\n')
                : (div.textContent || '').replace(/\s+/g, ' ').trim();

            if (bookInfo?.bookName) {
                bookName = bookInfo.bookName;
            }

            return {
                chapterId: chapterInfo.chapterId,
                chapterName: chapterInfo.chapterName,
                content: content,
                bookId: bookInfo?.bookId,
                nextChapterId: chapterInfo.next
            };
        } catch (e) {
            console.error('解析章节信息失败:', e);
            return null;
        }
    }

    // 导出章节
    function exportChapter(chapterName, content) {
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const filename = bookName ? `${bookName}_${chapterName}.txt` : `${chapterName}.txt`;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // 通过服务器保存章节
    async function saveToServer(bookName, chapterName, chapterId, content) {
        try {
            const query = chapterId ? `?chapter_id=${encodeURIComponent(chapterId)}` : '';
            const response = await fetch(`${API_BASE}/save/${encodeURIComponent(bookName)}/${encodeURIComponent(chapterName)}${query}`, {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain;charset=utf-8' },
                body: content
            });
            if (!response.ok) {
                const detail = await response.json().catch(() => null);
                throw new Error(detail?.detail || `HTTP ${response.status}`);
            }
            return true;
        } catch (e) {
            alert('保存失败: ' + e.message);
            return false;
        }
    }

    // 创建按钮容器
    const container = document.createElement('div');
    container.style.cssText = `
        position: fixed;
        top: 50%;
        right: 20px;
        transform: translateY(-50%);
        display: flex;
        flex-direction: column;
        gap: 12px;
        z-index: 99999;
    `;
    document.body.appendChild(container);

    // 导出按钮
    const exportBtn = document.createElement('div');
    exportBtn.innerHTML = '📥 导出';
    exportBtn.style.cssText = `
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        padding: 12px 18px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(231, 76, 60, 0.4);
        transition: all 0.3s ease;
        user-select: none;
    `;
    container.appendChild(exportBtn);

    // 下一章按钮
    const nextBtn = document.createElement('div');
    nextBtn.innerHTML = '▶ 下一章';
    nextBtn.style.cssText = `
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        padding: 12px 18px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(52, 152, 219, 0.4);
        transition: all 0.3s ease;
        user-select: none;
    `;
    container.appendChild(nextBtn);

    // 上一章按钮
    const prevBtn = document.createElement('div');
    prevBtn.innerHTML = '◀ 上一章';
    prevBtn.style.cssText = `
        background: linear-gradient(135deg, #95a5a6, #7f8c8d);
        color: white;
        padding: 12px 18px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(149, 165, 166, 0.4);
        transition: all 0.3s ease;
        user-select: none;
    `;
    container.appendChild(prevBtn);

    // 自动导出按钮
    const autoBtn = document.createElement('div');
    autoBtn.innerHTML = '🚀 自动';
    autoBtn.style.cssText = `
        background: linear-gradient(135deg, #22c55e, #16a34a);
        color: white;
        padding: 12px 18px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
        transition: all 0.3s ease;
        user-select: none;
    `;
    container.appendChild(autoBtn);

    // 停止按钮
    const stopBtn = document.createElement('div');
    stopBtn.innerHTML = '⏹ 停止';
    stopBtn.style.cssText = `
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
        padding: 12px 18px;
        border-radius: 25px;
        cursor: pointer;
        font-size: 14px;
        font-weight: bold;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.4);
        transition: all 0.3s ease;
        user-select: none;
        display: none;
    `;
    container.appendChild(stopBtn);

    // 状态显示 - 独立飘窗
    const statusDiv = document.createElement('div');
    statusDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: rgba(0,0,0,0.85);
        color: #4ade80;
        padding: 16px 20px;
        border-radius: 12px;
        font-size: 14px;
        z-index: 99999;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        display: none;
        min-width: 180px;
    `;
    document.body.appendChild(statusDiv);

    // 清除状态按钮
    const clearBtn = document.createElement('div');
    clearBtn.innerHTML = '🗑 清除';
    clearBtn.style.cssText = `
        background: rgba(100,100,100,0.8);
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.3s ease;
        user-select: none;
    `;
    container.appendChild(clearBtn);

    // 悬停效果
    [exportBtn, autoBtn, stopBtn, nextBtn, prevBtn, clearBtn].forEach(btn => {
        btn.addEventListener('mouseenter', () => btn.style.transform = 'scale(1.1)');
        btn.addEventListener('mouseleave', () => btn.style.transform = 'scale(1)');
    });

    // 更新UI状态
    function updateUI() {
        if (isAutoRunning) {
            autoBtn.style.display = 'none';
            stopBtn.style.display = 'block';
            statusDiv.style.display = 'block';
            statusDiv.innerHTML = `🚚 ${bookName}<br>已导出: ${exportedCount} 章`;
        } else {
            autoBtn.style.display = 'block';
            stopBtn.style.display = 'none';
            if (exportedCount > 0) {
                statusDiv.style.display = 'block';
                statusDiv.innerHTML = `✅ 已暂停<br>已导出: ${exportedCount} 章`;
            }
        }
    }

    // 导出当前章节
    async function exportCurrentChapter() {
        const info = getChapterInfo();
        if (!info || !info.content) {
            alert('无法获取章节内容');
            return false;
        }
        // 等待服务器保存成功
        const success = await saveToServer(
            bookName || '未知书名',
            info.chapterName,
            info.chapterId,
            info.content
        );
        if (!success) {
            return false;
        }
        exportedCount++;
        saveState();
        updateUI();
        return info;
    }

    // 自动导出流程
    async function startAutoExport() {
        isAutoRunning = true;
        saveState();
        updateUI();

        while (isAutoRunning) {
            const info = await exportCurrentChapter();
            if (!info) {
                // 保存失败，停止
                isAutoRunning = false;
                saveState();
                updateUI();
                break;
            }

            // 按钮反馈
            autoBtn.innerHTML = '✅ 已导出';
            setTimeout(() => { if (!isAutoRunning) autoBtn.innerHTML = '🚀 自动'; }, 500);

            // 翻页
            if (info.bookId && info.nextChapterId) {
                saveState();
                window.location.assign(`https://www.qidian.com/chapter/${info.bookId}/${info.nextChapterId}/`);
            } else {
                isAutoRunning = false;
                saveState();
                updateUI();
                alert(`导出完成！共 ${exportedCount} 章`);
                break;
            }
        }
    }

    function stopAutoExport() {
        isAutoRunning = false;
        saveState();
        autoBtn.innerHTML = '🚀 自动';
        updateUI();
    }

    // 事件绑定
    exportBtn.addEventListener('click', () => {
        const info = getChapterInfo();
        if (!info || !info.content) {
            alert('无法获取章节内容');
            return;
        }
        exportChapter(info.chapterName, info.content);
        exportBtn.innerHTML = '✅ 已导出';
        setTimeout(() => { exportBtn.innerHTML = '📥 导出'; }, 1500);
    });

    autoBtn.addEventListener('click', startAutoExport);
    stopBtn.addEventListener('click', stopAutoExport);
    clearBtn.addEventListener('click', () => {
        localStorage.removeItem(STORAGE_KEY);
        isAutoRunning = false;
        exportedCount = 0;
        bookName = '';
        updateUI();
        statusDiv.style.display = 'none';
        alert('已清除状态');
    });

    nextBtn.addEventListener('click', () => {
        const links = document.querySelectorAll('a[href*="/chapter/"]');
        links.forEach(link => {
            if (link.textContent.includes('下一章') || link.textContent === '下一章') {
                window.location.href = link.href;
            }
        });
    });

    prevBtn.addEventListener('click', () => {
        const links = document.querySelectorAll('a[href*="/chapter/"]');
        links.forEach(link => {
            if (link.textContent.includes('上一章') || link.textContent === '上一章') {
                window.location.href = link.href;
            }
        });
    });

    // 初始化
    loadState();
    updateUI();

    // 如果之前在自动导出，页面加载后自动继续
    if (isAutoRunning && exportedCount > 0) {
        statusDiv.style.display = 'block';
        statusDiv.innerHTML = `🚚 继续导出...<br>已导出: ${exportedCount} 章`;
        // 延迟执行，等页面完全加载
        setTimeout(() => {
            startAutoExport();
        }, 1000);
    }
})();
