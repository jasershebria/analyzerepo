import {
  Component,
  Input,
  OnChanges,
  AfterViewInit,
  ViewChild,
  ElementRef,
  SimpleChanges,
} from '@angular/core';
import mermaid from 'mermaid';

@Component({
  selector: 'app-flowchart-viewer',
  standalone: false,
  templateUrl: './flowchart-viewer.component.html',
  styleUrl: './flowchart-viewer.component.scss',
})
export class FlowchartViewerComponent implements OnChanges, AfterViewInit {
  @Input() mermaidCode = '';
  @ViewChild('container') containerRef!: ElementRef<HTMLDivElement>;

  zoom = 1;
  private initialized = false;

  ngAfterViewInit(): void {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'dark',
      themeVariables: {
        primaryColor: '#6366F1',
        primaryTextColor: '#E5E7EB',
        primaryBorderColor: '#6366F1',
        lineColor: '#9CA3AF',
        secondaryColor: '#111827',
        tertiaryColor: '#1f2937',
        background: '#0B0F14',
        mainBkg: '#111827',
        textColor: '#E5E7EB',
        border1: '#374151',
        fontFamily: 'Inter, sans-serif',
      },
    });
    this.initialized = true;
    if (this.mermaidCode) this.renderChart();
  }

  ngOnChanges(_changes: SimpleChanges): void {
    if (this.initialized && this.mermaidCode) this.renderChart();
  }

  async renderChart(): Promise<void> {
    if (!this.containerRef?.nativeElement || !this.mermaidCode) return;
    const id = `mermaid-${Date.now()}`;
    try {
      const { svg } = await mermaid.render(id, this.mermaidCode);
      this.containerRef.nativeElement.innerHTML = svg;
    } catch {
      this.containerRef.nativeElement.innerHTML =
        '<p style="color:#EF4444;padding:1rem">Error rendering flowchart</p>';
    }
  }

  zoomIn(): void {
    this.zoom = Math.min(this.zoom + 0.2, 2);
  }

  zoomOut(): void {
    this.zoom = Math.max(this.zoom - 0.2, 0.5);
  }

  get zoomPercent(): number {
    return Math.round(this.zoom * 100);
  }

  downloadSvg(): void {
    const svg = this.containerRef?.nativeElement.querySelector('svg');
    if (!svg) return;
    const data = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([data], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flowchart.svg';
    a.click();
    URL.revokeObjectURL(url);
  }
}
