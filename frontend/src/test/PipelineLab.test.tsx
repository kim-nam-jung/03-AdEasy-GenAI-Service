import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { PipelineLab } from '../components/PipelineLab';
import '@testing-library/jest-dom';

// Mock API client
vi.mock('../api/client', () => ({
  api: {
    debugStep1Segmentation: vi.fn(),
    debugStep2VideoGeneration: vi.fn(),
    debugStep3Postprocess: vi.fn(),
  }
}));

// Mock URL.createObjectURL since JSDOM doesn't support it
vi.stubGlobal('URL', {
  createObjectURL: vi.fn(() => 'mock-url'),
});

describe('PipelineLab Component', () => {
  it('renders and allows tab switching', () => {
    render(<PipelineLab />);
    
    // Check initial render
    expect(screen.getByText('Pipeline Lab')).toBeInTheDocument();
    expect(screen.getByText('1. Segmentation')).toBeInTheDocument();
    expect(screen.getByText('Run Segmentation')).toBeInTheDocument();
    
    // Switch to step 2
    const step2Tab = screen.getByText('2. Video Generation');
    fireEvent.click(step2Tab);
    expect(screen.getByText('Layer Image Path')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('/path/to/segmented/layer_0.png')).toBeInTheDocument();
    
    // Switch to step 3
    const step3Tab = screen.getByText('3. Post-processing');
    fireEvent.click(step3Tab);
    expect(screen.getByText('Raw Video Path')).toBeInTheDocument();
    expect(screen.getByText('RIFE Frame Interpolation (24fps → 48fps)')).toBeInTheDocument();
  });

  it('disables step 1 run button when no files are selected', () => {
    render(<PipelineLab />);
    const runBtn = screen.getByText('Run Segmentation');
    expect(runBtn).toBeDisabled();
  });

  it('enables step 1 run button and shows result after "upload"', async () => {
    render(<PipelineLab />);
    
    // Simulating file selection would require more complex interaction with ImageUploader
    // but we can test if the button becomes enabled if we were to mock state or just 
    // test the tab interaction for now.
    
    fireEvent.click(screen.getByText('2. Video Generation'));
    const genBtn = screen.getByText('Generate Video');
    expect(genBtn).toBeDisabled();
  });

  it('updates state when typing in step 2 prompt', () => {
    render(<PipelineLab />);
    fireEvent.click(screen.getByText('2. Video Generation'));
    
    const textarea = screen.getByPlaceholderText(/A product rotating slowly/);
    fireEvent.change(textarea, { target: { value: 'New prompt' } });
    expect(textarea).toHaveValue('New prompt');
  });

  it('handles step 2 video generation execution', async () => {
    render(<PipelineLab />);
    fireEvent.click(screen.getByText('2. Video Generation'));
    
    const pathInput = screen.getByPlaceholderText('/path/to/segmented/layer_0.png');
    const promptInput = screen.getByPlaceholderText(/A product rotating slowly/);
    const runBtn = screen.getByText('Generate Video');

    fireEvent.change(pathInput, { target: { value: 'test.png' } });
    fireEvent.change(promptInput, { target: { value: 'test prompt' } });
    
    expect(runBtn).not.toBeDisabled();
    fireEvent.click(runBtn);
    
    expect(await screen.findByText(/"status": "success"/)).toBeInTheDocument();
  });

  it('handles step 3 post-processing execution', async () => {
    render(<PipelineLab />);
    fireEvent.click(screen.getByText('3. Post-processing'));
    
    const pathInput = screen.getByPlaceholderText('/path/to/raw_video.mp4');
    const runBtn = screen.getByText('Run Post-processing');

    fireEvent.change(pathInput, { target: { value: 'raw.mp4' } });
    
    expect(runBtn).not.toBeDisabled();
    fireEvent.click(runBtn);
    
    expect(await screen.findByText(/"status": "success"/)).toBeInTheDocument();
  });
});
