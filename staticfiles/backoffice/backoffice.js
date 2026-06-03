document.addEventListener('DOMContentLoaded', () => {
    const content = document.getElementById('backoffice-content');
    const sidebarButtons = document.querySelectorAll('[data-url]');

    let currentSectionUrl = null;

    if (!content) {
        return;
    }

    function normalizeUrl(url) {
        if (!url) {
            return '';
        }

        try {
            return new URL(url, window.location.origin).pathname;
        } catch (error) {
            return url;
        }
    }

    function getCurrentPageUrl() {
        return window.location.pathname + window.location.search;
    }

    function setActiveSidebarButton(activeButton) {
        sidebarButtons.forEach((button) => {
            button.classList.remove('is-active');
        });

        if (activeButton) {
            activeButton.classList.add('is-active');
        }
    }

    function setActiveSidebarButtonByUrl(url) {
        const normalizedTargetUrl = normalizeUrl(url);

        let matchedButton = null;

        sidebarButtons.forEach((button) => {
            const buttonUrl = normalizeUrl(button.dataset.url);

            if (buttonUrl && normalizedTargetUrl.startsWith(buttonUrl)) {
                matchedButton = button;
            }
        });

        if (matchedButton) {
            setActiveSidebarButton(matchedButton);
        }
    }

    function isFullPageHtml(html) {
        const normalizedHtml = html.toLowerCase();

        return (
            normalizedHtml.includes('<html') ||
            normalizedHtml.includes('<body') ||
            normalizedHtml.includes('id="backoffice-content"') ||
            normalizedHtml.includes("id='backoffice-content'")
        );
    }

    function hasFormErrors(html) {
        const normalizedHtml = html.toLowerCase();

        return (
            normalizedHtml.includes('errorlist') ||
            normalizedHtml.includes('alert-error') ||
            normalizedHtml.includes('dashboard-message-error') ||
            normalizedHtml.includes('este campo es obligatorio') ||
            normalizedHtml.includes('this field is required')
        );
    }

    function getParentUrlFromContent() {
        const elementWithParentUrl = content.querySelector('[data-parent-url]');

        if (!elementWithParentUrl) {
            return null;
        }

        return elementWithParentUrl.dataset.parentUrl || null;
    }

    function updateCurrentSectionFromContent(fallbackUrl) {
        const parentUrl = getParentUrlFromContent();

        if (parentUrl) {
            currentSectionUrl = parentUrl;
            setActiveSidebarButtonByUrl(parentUrl);
            return;
        }

        currentSectionUrl = fallbackUrl;
        setActiveSidebarButtonByUrl(fallbackUrl);
    }

    function updateBrowserHistory(url, replaceHistory) {
        if (!url) {
            return;
        }

        const state = {
            backofficeUrl: url,
        };

        if (replaceHistory) {
            window.history.replaceState(state, '', url);
            return;
        }

        window.history.pushState(state, '', url);
    }

    function replaceContentOrRedirect(html, response, loadedUrl) {
        if (isFullPageHtml(html)) {
            window.location.href = response.url;
            return;
        }

        content.innerHTML = html;
        bindDynamicContent();
        updateCurrentSectionFromContent(loadedUrl);
    }

    function getFormReturnUrl(form) {
        const explicitParentUrl = form.dataset.parentUrl;

        if (explicitParentUrl) {
            return explicitParentUrl;
        }

        const explicitReturnUrl = form.dataset.returnUrl;

        if (explicitReturnUrl) {
            return explicitReturnUrl;
        }

        const cancelLink = form.querySelector('[data-ajax-link]');

        if (cancelLink) {
            const cancelUrl = cancelLink.getAttribute('href');

            if (cancelUrl) {
                return cancelUrl;
            }
        }

        if (currentSectionUrl) {
            return currentSectionUrl;
        }

        return null;
    }

    async function loadSection(url, options = {}) {
        const shouldPushHistory = options.pushHistory !== false;
        const shouldReplaceHistory = options.replaceHistory === true;

        try {
            const response = await fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error('No se pudo cargar la sección');
            }

            const html = await response.text();

            replaceContentOrRedirect(html, response, url);

            if (!isFullPageHtml(html) && shouldPushHistory) {
                updateBrowserHistory(url, shouldReplaceHistory);
            }
        } catch (error) {
            content.innerHTML = `
                <div class="dashboard-messages">
                    <div class="dashboard-message dashboard-message-error">
                        <span class="dashboard-message-icon">!</span>
                        <span class="dashboard-message-text">Error al cargar el contenido.</span>
                    </div>
                </div>
            `;
        }
    }

    async function submitForm(form) {
        const formData = new FormData(form);
        const submitButton = form.querySelector('button[type="submit"]');
        const originalButtonText = submitButton ? submitButton.textContent : '';
        const returnUrl = getFormReturnUrl(form);

        try {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = 'Guardando...';
            }

            const response = await fetch(form.action, {
                method: form.method || 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            });

            if (!response.ok) {
                throw new Error('No se pudo enviar el formulario');
            }

            const html = await response.text();

            /*
                Si Django devuelve el formulario con errores,
                mostramos esos errores y NO volvemos a la lista padre.
            */
            if (hasFormErrors(html)) {
                replaceContentOrRedirect(html, response, response.url || form.action);
                return;
            }

            /*
                Si Django ha devuelto una página completa,
                no la incrustamos dentro del backoffice actual.
            */
            if (isFullPageHtml(html)) {
                window.location.href = response.url;
                return;
            }

            /*
                Si el guardado ha ido bien, volvemos a la sección padre
                del formulario y sustituimos la URL del formulario en el historial.
            */
            if (returnUrl) {
                await loadSection(returnUrl, {
                    replaceHistory: true,
                });
                return;
            }

            replaceContentOrRedirect(html, response, response.url || form.action);
        } catch (error) {
            content.insertAdjacentHTML(
                'afterbegin',
                `
                    <div class="dashboard-messages">
                        <div class="dashboard-message dashboard-message-error">
                            <span class="dashboard-message-icon">!</span>
                            <span class="dashboard-message-text">Error al guardar los cambios.</span>
                        </div>
                    </div>
                `
            );

            if (submitButton) {
                submitButton.disabled = false;
                submitButton.textContent = originalButtonText;
            }
        }
    }

    function bindDynamicLinks() {
        const ajaxLinks = content.querySelectorAll('[data-ajax-link]');

        ajaxLinks.forEach((link) => {
            link.addEventListener('click', (event) => {
                event.preventDefault();

                const url = link.getAttribute('href');

                if (!url) {
                    return;
                }

                const form = link.closest('form');
                const parentUrl = form ? getFormReturnUrl(form) : null;
                const isBackToParentLink = parentUrl && normalizeUrl(url) === normalizeUrl(parentUrl);

                loadSection(url, {
                    replaceHistory: isBackToParentLink,
                });
            });
        });
    }

    function bindDynamicForms() {
        const ajaxForms = content.querySelectorAll('form');

        ajaxForms.forEach((form) => {
            form.addEventListener('submit', (event) => {
                if (event.defaultPrevented || event.returnValue === false) {
                    return;
                }

                const confirmMessage = form.dataset.confirm;

                if (confirmMessage && !window.confirm(confirmMessage)) {
                    event.preventDefault();
                    return;
                }

                event.preventDefault();
                submitForm(form);
            });
        });
    }

    function bindDynamicContent() {
        bindDynamicLinks();
        bindDynamicForms();
    }

    sidebarButtons.forEach((button) => {
        button.addEventListener('click', () => {
            const url = button.dataset.url;

            if (url) {
                loadSection(url);
            }
        });
    });

    window.addEventListener('popstate', (event) => {
        const url = event.state && event.state.backofficeUrl
            ? event.state.backofficeUrl
            : getCurrentPageUrl();

        loadSection(url, {
            pushHistory: false,
        });
    });

    bindDynamicContent();

    const initialUrl = getCurrentPageUrl();
    const initialParentUrl = getParentUrlFromContent();

    if (initialParentUrl) {
        currentSectionUrl = initialParentUrl;
        setActiveSidebarButtonByUrl(initialParentUrl);
    } else {
        currentSectionUrl = initialUrl;
        setActiveSidebarButtonByUrl(initialUrl);

        if (!document.querySelector('.sidebar-nav-button.is-active') && sidebarButtons.length > 0) {
            const firstButton = sidebarButtons[0];
            currentSectionUrl = firstButton.dataset.url;
            setActiveSidebarButton(firstButton);
        }
    }

    window.history.replaceState(
        {
            backofficeUrl: initialUrl,
        },
        '',
        initialUrl
    );
});