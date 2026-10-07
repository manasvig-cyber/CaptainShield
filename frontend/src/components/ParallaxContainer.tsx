import React from 'react';

interface ParallaxContainerProps {
  children: React.ReactNode;
}

export const ParallaxContainer: React.FC<ParallaxContainerProps> = ({ children }) => {
  return (
    <div className="command-center-canvas">
      {/* Main Stationary Dashboard Container */}
      <div className="dashboard-viewport">
        {/* Subtle Top Edge Glow */}
        <div className="dashboard-top-shine" />

        {/* Interior Application Viewport */}
        {children}
      </div>
    </div>
  );
};
