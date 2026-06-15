"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

interface OCREntry {
  text?: string;
  confidence?: number;
  bbox?: number[][];
  page_number?: number;
  is_headline?: boolean;
  matched_keyword?: string | null;
}

interface ViewerResponse {
  image_url: string;
  matched_entries?: OCREntry[];
  ocr_entries?: OCREntry[];
  total_matches?: number;
  page_number: number;
  document_id: string;
}

export default function ViewerPage() {
  const params = useParams();
  const documentId = params?.documentId as string;
  const page = Number(params?.page);
  const [viewerData, setViewerData] = useState<ViewerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scaleX, setScaleX] = useState(1);
  const [scaleY, setScaleY] = useState(1);
  const [isSnippetMode, setIsSnippetMode] = useState(false);
  const [selectionRect, setSelectionRect] = useState<{ x: number; y: number; width: number; height: number } | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const imageRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const isSelectingRef = useRef(false);

  useEffect(() => {
    if (isSnippetMode) {
      document.body.style.cursor = "crosshair";
      return () => {
        document.body.style.cursor = "default";
      };
    }
  }, [isSnippetMode]);

  useEffect(() => {
    const fetchViewerData = async () => {
      try {
        setLoading(true);
        if (!documentId || Number.isNaN(page) || page < 1) {
          throw new Error("Invalid viewer params");
        }

        const response = await axios.get<ViewerResponse & { ocr_entries?: OCREntry[] }>(`${API_BASE}/viewer/${documentId}/${page}`);
        console.log("VIEWER RESPONSE", response.data);
        setViewerData(response.data);
        setError(null);
      } catch (err: unknown) {
        console.error("Failed to load viewer data:", err);
        const axiosErr = err as { response?: { data?: unknown } };
        const message = axiosErr?.response?.data ? JSON.stringify(axiosErr.response?.data) : "Failed to load viewer data";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    fetchViewerData();
  }, [documentId, page]);

  useEffect(() => {
    if (!imageRef.current) return;

    const calculateScale = () => {
      const img = imageRef.current;
      if (!img) return;

      const imgWidth = img.naturalWidth;
      const imgHeight = img.naturalHeight;
      const containerWidth = img.offsetWidth;
      const containerHeight = img.offsetHeight;

      if (imgWidth > 0 && imgHeight > 0 && containerWidth > 0 && containerHeight > 0) {
        setScaleX(containerWidth / imgWidth);
        setScaleY(containerHeight / imgHeight);
      }
    };

    const timeoutId = window.setTimeout(calculateScale, 100);
    const observer = new ResizeObserver(calculateScale);
    if (imageRef.current.parentElement) {
      observer.observe(imageRef.current.parentElement);
    }

    return () => {
      window.clearTimeout(timeoutId);
      observer.disconnect();
    };
  }, [viewerData]);

  useEffect(() => {
    if (!isSnippetMode) return;

    const container = containerRef.current;
    if (!container) return;

    const handleMouseDown = (e: MouseEvent) => {
      if (e.button !== 0) return;
      e.preventDefault();
      const rect = container.getBoundingClientRect();
      if (!rect) return;

      console.log("mousedown: clientX=" + e.clientX + ", clientY=" + e.clientY + ", rectX=" + rect.left + ", rectY=" + rect.top);

      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      dragStartRef.current = { x, y };
      isSelectingRef.current = true;
      setIsSelecting(true);

      setSelectionRect({
        x,
        y,
        width: 0,
        height: 0,
      });
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isSelectingRef.current) return;
      e.preventDefault();
      const rect = container.getBoundingClientRect();
      if (!rect) return;

      const currentX = e.clientX - rect.left;
      const currentY = e.clientY - rect.top;
      const startX = dragStartRef.current.x;
      const startY = dragStartRef.current.y;

      console.log("mousemove: currentX=" + currentX + ", currentY=" + currentY);

      const minX = Math.min(startX, currentX);
      const maxX = Math.max(startX, currentX);
      const minY = Math.min(startY, currentY);
      const maxY = Math.max(startY, currentY);

      setSelectionRect({
        x: minX,
        y: minY,
        width: maxX - minX,
        height: maxY - minY,
      });
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (!isSelectingRef.current) return;
      console.log("mouseup: clientX=" + e.clientX + ", clientY=" + e.clientY);
      isSelectingRef.current = false;
      setIsSelecting(false);
    };

    const handleMouseLeave = (e: MouseEvent) => {
      if (!isSelectingRef.current) return;
      console.log("mouseleave");
      isSelectingRef.current = false;
      setIsSelecting(false);
    };

    container.addEventListener("mousedown", handleMouseDown);
    container.addEventListener("mousemove", handleMouseMove);
    container.addEventListener("mouseleave", handleMouseLeave);
    window.addEventListener("mouseup", handleMouseUp);

    return () => {
      container.removeEventListener("mousedown", handleMouseDown);
      container.removeEventListener("mousemove", handleMouseMove);
      container.removeEventListener("mouseleave", handleMouseLeave);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isSnippetMode]);

  const convertOriginalToDisplayCoords = (originalX: number, originalY: number) => {
    return {
      x: originalX * scaleX,
      y: originalY * scaleY,
    };
  };

  const convertDisplayToOriginalCoords = (displayX: number, displayY: number) => {
    return {
      x: displayX / scaleX,
      y: displayY / scaleY,
    };
  };

  const cropSnippet = () => {
    if (!selectionRect || !imageRef.current || !canvasRef.current) return null;

    console.log("COPY CLICKED / DOWNLOAD CLICKED — cropSnippet called");
    console.log("selectionRect:", selectionRect);

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;

    const originalImg = imageRef.current;
    const naturalWidth = originalImg.naturalWidth;
    const naturalHeight = originalImg.naturalHeight;
    const displayedWidth = originalImg.offsetWidth;
    const displayedHeight = originalImg.offsetHeight;

    console.log("displayedWidth:", displayedWidth, "displayedHeight:", displayedHeight);
    console.log("naturalWidth:", naturalWidth, "naturalHeight:", naturalHeight);
    console.log("scaleX:", scaleX, "scaleY:", scaleY);

    if (naturalWidth === 0 || naturalHeight === 0) return null;

    const cropX = selectionRect.x / scaleX;
    const cropY = selectionRect.y / scaleY;
    const cropWidth = selectionRect.width / scaleX;
    const cropHeight = selectionRect.height / scaleY;

    console.log("cropX:", cropX, "cropY:", cropY, "cropWidth:", cropWidth, "cropHeight:", cropHeight);

    if (cropWidth <= 0 || cropHeight <= 0) return null;

    canvas.width = cropWidth;
    canvas.height = cropHeight;

    ctx.drawImage(
      originalImg,
      cropX, cropY, cropWidth, cropHeight,
      0, 0, cropWidth, cropHeight
    );

    return canvas.toDataURL("image/png");
  };

  const downloadSnippet = () => {
    console.log("DOWNLOAD CLICKED");
    const imageData = cropSnippet();
    if (!imageData) return;

    const link = document.createElement("a");
    link.download = `snippet_${documentId}_page${page}.png`;
    link.href = imageData;
    link.click();
  };

  const copySnippet = async () => {
    console.log("COPY CLICKED");
    const imageData = cropSnippet();
    if (!imageData) return;

    try {
      const response = await fetch(imageData);
      const blob = await response.blob();
      await navigator.clipboard.write([
        new ClipboardItem({ "image/png": blob })
      ]);
    } catch (err) {
      console.error("Failed to copy image:", err);
    }
  };

  const clearSelection = () => {
    console.log("CANCEL CLICKED");
    setSelectionRect(null);
    setIsSelecting(false);
    isSelectingRef.current = false;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <div className="text-lg">Loading viewer...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <div className="text-lg text-red-500">Error: {error}</div>
      </div>
    );
  }

  if (!viewerData) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center text-white">
        <div className="text-lg">No data available</div>
      </div>
    );
  }

  const matchedEntries = viewerData.matched_entries ?? [];

  return (
    <div className="min-h-screen bg-black">
      <div className="relative w-full" ref={containerRef} style={{ cursor: isSnippetMode ? "crosshair" : "default" }}>
        <img
          ref={imageRef}
          src={viewerData.image_url}
          alt={`Document ${viewerData.document_id} - Page ${viewerData.page_number}`}
          className="w-full h-auto block"
          crossOrigin="anonymous"
          onError={(e) => {
            console.error("Failed to load image:", e);
            (e.target as HTMLImageElement).style.display = "none";
          }}
        />

        {selectionRect && (
          <div
            className="absolute"
            style={{
              left: `${selectionRect.x}px`,
              top: `${selectionRect.y}px`,
              width: `${selectionRect.width}px`,
              height: `${selectionRect.height}px`,
              border: "2px solid #00aaff",
              backgroundColor: "rgba(0,170,255,0.15)",
              pointerEvents: "none",
              zIndex: 1000,
            }}
          />
        )}

        {matchedEntries.map((entry, index) => {
          if (!entry.bbox) return null;

          const bbox = entry.bbox;
          const xs = bbox.map(point => point[0]);
          const ys = bbox.map(point => point[1]);
          const left = Math.min(...xs) * scaleX;
          const top = Math.min(...ys) * scaleY;
          const width = (Math.max(...xs) - Math.min(...xs)) * scaleX;
          const height = (Math.max(...ys) - Math.min(...ys)) * scaleY;

          return (
            <div
              key={index}
              aria-hidden
              className="absolute leading-tight"
              style={{
                left: `${left}px`,
                top: `${top}px`,
                width: `${width}px`,
                height: `${height}px`,
                backgroundColor: "rgba(255,255,0,0.45)",
                border: "1px solid rgba(255,165,0,0.95)",
                boxSizing: "border-box",
                overflow: "hidden",
                userSelect: "none",
                pointerEvents: "none",
              }}
            />
          );
        })}

        {matchedEntries.length === 0 && (
          <div className="absolute inset-x-0 bottom-4 text-center text-sm text-white/80">
            No matched OCR entries for this page.
          </div>
        )}

        <canvas
          ref={canvasRef}
          className="hidden"
        />
      </div>

      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={() => setIsSnippetMode(!isSnippetMode)}
          className={
            isSnippetMode
              ? "px-4 py-2 rounded font-medium transition-colors bg-red-600 text-white hover:bg-red-700"
              : "px-4 py-2 rounded font-medium transition-colors bg-white text-black hover:bg-gray-100"
          }
        >
          {isSnippetMode ? "Exit Snippet Mode" : "Snippet Mode"}
        </button>

        {selectionRect && (
          <div className="flex gap-2">
            <button
              onClick={copySnippet}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 font-medium"
            >
              Copy Image
            </button>
            <button
              onClick={downloadSnippet}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 font-medium"
            >
              Download PNG
            </button>
            <button
              onClick={clearSelection}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 font-medium"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
