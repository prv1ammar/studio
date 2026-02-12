import React from 'react';

export default function CollaborationOverlay({ collaborators }) {
    return (
        <div className="collaboration-overlay">
            {Object.entries(collaborators).map(([userId, data]) => (
                data.cursor && (
                    <div
                        key={userId}
                        className="live-cursor"
                        style={{
                            left: data.cursor.x,
                            top: data.cursor.y,
                            position: 'fixed',
                            zIndex: 9999,
                            pointerEvents: 'none'
                        }}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="var(--primary-glow)">
                            <path d="M5.64 1.34l12.72 12.72-5.66 5.66-3.54-3.54-3.52 3.52L1.4 15.46l3.52-3.52-3.54-3.54L5.64 1.34z" />
                        </svg>
                        <div className="cursor-label">
                            {data.name || userId || 'Collaborator'}
                        </div>
                    </div>
                )
            ))}
        </div>
    );
}
