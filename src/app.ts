// Main application bundle - utilities and initialization

/**
 * Initialize the application
 */
function initializeApp(): void {}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  // DOM is already ready
  initializeApp();
}
