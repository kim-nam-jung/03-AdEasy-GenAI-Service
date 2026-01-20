import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ProgressBar } from '../components/ProgressBar';

describe('ProgressBar', () => {
  it('renders correctly with given progress', () => {
    render(
      <ProgressBar 
        progress={50} 
        currentStep={1} 
        status="processing" 
        message="Generating video..." 
      />
    );
    
    // Check progress text
    expect(screen.getByText('50%')).toBeInTheDocument();
    
    // Check message
    expect(screen.getByText('Generating video...')).toBeInTheDocument();
    
    // Check step indicator (Step 2 is current, so it should be visible)
    expect(screen.getByText('Video Generation')).toBeInTheDocument();
    
    // Check step count
    expect(screen.getByText('STEP 2/3')).toBeInTheDocument();
  });

  it('shows checkmark for completed steps', () => {
    render(
      <ProgressBar 
        progress={100} 
        currentStep={3} 
        status="completed" 
        message="Done" 
      />
    );
    
    // All 3 steps should have checkmarks
    screen.getAllByText('✓');
    // Check for "Done" (might appear multiple times: status and message)
    const doneElements = screen.getAllByText('Done');
    expect(doneElements.length).toBeGreaterThan(0);
  });
});
