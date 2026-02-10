// API Configuration for Studio
// Automatically detects the host to allow the project to work on local network (multi-PC)

const getBaseUrl = () => {
    // If we are in local development, we use the hostname of the page
    // This allows other PCs on the network to connect to the backend on THIS PC
    const hostname = window.location.hostname;
    return `http://${hostname}:8000`;
};

export const API_BASE_URL = getBaseUrl();
