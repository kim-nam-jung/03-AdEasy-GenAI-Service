import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageUploader } from '../components/ImageUploader';
import '@testing-library/jest-dom';

// Mock URL.createObjectURL
vi.stubGlobal('URL', {
  createObjectURL: vi.fn(() => 'mock-url'),
});

describe('ImageUploader Component', () => {
  it('renders correctly', () => {
    render(<ImageUploader onImagesSelected={() => {}} isLoading={false} />);
    expect(screen.getByText('Drop files here or click to upload')).toBeInTheDocument();
  });

  it('shows loading state', () => {
    render(<ImageUploader onImagesSelected={() => {}} isLoading={true} />);
    const container = screen.getByText('Drop files here or click to upload').parentElement?.parentElement;
    expect(container).toHaveClass('cursor-not-allowed');
  });

  it('handles file selection', () => {
    const onImagesSelected = vi.fn();
    const { container } = render(<ImageUploader onImagesSelected={onImagesSelected} isLoading={false} />);
    
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File([''], 'test.png', { type: 'image/png' });
    
    // Simulate file change
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(onImagesSelected).toHaveBeenCalledWith([file]);
  });
});
