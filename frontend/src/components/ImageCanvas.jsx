import { useState, useEffect, useRef } from 'react';
import { Stage, Layer, Image, Line, Text, Group, Rect } from 'react-konva';
import { ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

/**
 * Interactive image canvas for viewing and editing roof dimensions.
 * Features: zoom, pan, editable dimension labels
 */
export default function ImageCanvas({
    imageUrl,
    dimensions,
    onDimensionsChange,
    pitchAngle = 35
}) {
    const containerRef = useRef(null);
    const [image, setImage] = useState(null);
    const [stageSize, setStageSize] = useState({ width: 600, height: 400 });
    const [scale, setScale] = useState(1);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [editingField, setEditingField] = useState(null);
    const [editValue, setEditValue] = useState('');

    // Load image
    useEffect(() => {
        if (!imageUrl) return;

        const img = new window.Image();
        img.crossOrigin = 'anonymous';
        img.src = imageUrl;
        img.onload = () => {
            setImage(img);

            // Fit image to container
            if (containerRef.current) {
                const containerWidth = containerRef.current.offsetWidth;
                const aspectRatio = img.width / img.height;
                const height = containerWidth / aspectRatio;
                setStageSize({
                    width: containerWidth,
                    height: Math.min(height, 500)
                });

                // Calculate initial scale to fit
                const scaleX = containerWidth / img.width;
                const scaleY = Math.min(height, 500) / img.height;
                setScale(Math.min(scaleX, scaleY, 1));
            }
        };
    }, [imageUrl]);

    // Handle container resize
    useEffect(() => {
        const handleResize = () => {
            if (containerRef.current) {
                setStageSize({
                    width: containerRef.current.offsetWidth,
                    height: stageSize.height
                });
            }
        };

        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, [stageSize.height]);

    // Zoom handlers
    const handleZoom = (direction) => {
        const newScale = direction === 'in'
            ? Math.min(scale * 1.2, 3)
            : Math.max(scale / 1.2, 0.3);
        setScale(newScale);
    };

    const handleWheel = (e) => {
        e.evt.preventDefault();
        const scaleBy = 1.1;
        const newScale = e.evt.deltaY < 0
            ? Math.min(scale * scaleBy, 3)
            : Math.max(scale / scaleBy, 0.3);
        setScale(newScale);
    };

    const handleReset = () => {
        setScale(1);
        setPosition({ x: 0, y: 0 });
    };

    // Dimension editing
    const handleDimensionClick = (field) => {
        setEditingField(field);
        setEditValue(dimensions[field]?.toString() || '');
    };

    const handleEditSubmit = () => {
        if (editingField && editValue) {
            const newValue = parseFloat(editValue);
            if (!isNaN(newValue) && newValue >= 2 && newValue <= 50) {
                onDimensionsChange({
                    ...dimensions,
                    [editingField]: newValue
                });
            }
        }
        setEditingField(null);
        setEditValue('');
    };

    const handleEditKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleEditSubmit();
        } else if (e.key === 'Escape') {
            setEditingField(null);
            setEditValue('');
        }
    };

    // Calculate positions for dimension lines
    const imageWidth = image?.width || 800;
    const imageHeight = image?.height || 600;

    // Position dimension labels
    const lengthLabelPos = {
        x: (imageWidth * scale) / 2,
        y: imageHeight * scale + 30
    };
    const widthLabelPos = {
        x: imageWidth * scale + 30,
        y: (imageHeight * scale) / 2
    };

    // Calculate areas
    const planArea = (dimensions.length || 0) * (dimensions.width || 0);
    const realArea = planArea / Math.cos((pitchAngle * Math.PI) / 180);

    return (
        <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => handleZoom('in')}
                        className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                        title="Powiększ"
                    >
                        <ZoomIn className="w-4 h-4 text-dark-300" />
                    </button>
                    <button
                        onClick={() => handleZoom('out')}
                        className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                        title="Pomniejsz"
                    >
                        <ZoomOut className="w-4 h-4 text-dark-300" />
                    </button>
                    <button
                        onClick={handleReset}
                        className="p-2 bg-dark-700 rounded-lg hover:bg-dark-600 transition-colors"
                        title="Resetuj widok"
                    >
                        <RotateCcw className="w-4 h-4 text-dark-300" />
                    </button>
                    <span className="text-sm text-dark-400 ml-2">
                        {Math.round(scale * 100)}%
                    </span>
                </div>
                <div className="text-sm text-dark-400">
                    Kliknij wymiar, aby edytować
                </div>
            </div>

            {/* Canvas Container */}
            <div
                ref={containerRef}
                className="relative rounded-xl overflow-hidden border border-dark-700 bg-dark-900"
                style={{ minHeight: '400px' }}
            >
                <Stage
                    width={stageSize.width}
                    height={stageSize.height}
                    scaleX={scale}
                    scaleY={scale}
                    x={position.x}
                    y={position.y}
                    draggable
                    onDragEnd={(e) => setPosition({ x: e.target.x(), y: e.target.y() })}
                    onWheel={handleWheel}
                >
                    <Layer>
                        {/* Background Image */}
                        {image && (
                            <Image
                                image={image}
                                width={imageWidth}
                                height={imageHeight}
                            />
                        )}

                        {/* Length dimension line (bottom) */}
                        <Group>
                            <Line
                                points={[20, imageHeight - 20, imageWidth - 20, imageHeight - 20]}
                                stroke="#3b82f6"
                                strokeWidth={2 / scale}
                            />
                            {/* End caps */}
                            <Line
                                points={[20, imageHeight - 30, 20, imageHeight - 10]}
                                stroke="#3b82f6"
                                strokeWidth={2 / scale}
                            />
                            <Line
                                points={[imageWidth - 20, imageHeight - 30, imageWidth - 20, imageHeight - 10]}
                                stroke="#3b82f6"
                                strokeWidth={2 / scale}
                            />
                            {/* Label background */}
                            <Rect
                                x={imageWidth / 2 - 40}
                                y={imageHeight - 35}
                                width={80}
                                height={24}
                                fill="rgba(15, 23, 42, 0.9)"
                                cornerRadius={4}
                            />
                            {/* Label text */}
                            <Text
                                x={imageWidth / 2 - 35}
                                y={imageHeight - 30}
                                text={`${dimensions.length || 0} m`}
                                fontSize={14 / scale}
                                fill="#60a5fa"
                                fontStyle="bold"
                                onClick={() => handleDimensionClick('length')}
                                onTap={() => handleDimensionClick('length')}
                            />
                        </Group>

                        {/* Width dimension line (right side) */}
                        <Group>
                            <Line
                                points={[imageWidth - 20, 20, imageWidth - 20, imageHeight - 40]}
                                stroke="#22c55e"
                                strokeWidth={2 / scale}
                            />
                            {/* End caps */}
                            <Line
                                points={[imageWidth - 30, 20, imageWidth - 10, 20]}
                                stroke="#22c55e"
                                strokeWidth={2 / scale}
                            />
                            <Line
                                points={[imageWidth - 30, imageHeight - 40, imageWidth - 10, imageHeight - 40]}
                                stroke="#22c55e"
                                strokeWidth={2 / scale}
                            />
                            {/* Label background */}
                            <Rect
                                x={imageWidth - 60}
                                y={imageHeight / 2 - 12}
                                width={70}
                                height={24}
                                fill="rgba(15, 23, 42, 0.9)"
                                cornerRadius={4}
                            />
                            {/* Label text */}
                            <Text
                                x={imageWidth - 55}
                                y={imageHeight / 2 - 7}
                                text={`${dimensions.width || 0} m`}
                                fontSize={14 / scale}
                                fill="#4ade80"
                                fontStyle="bold"
                                onClick={() => handleDimensionClick('width')}
                                onTap={() => handleDimensionClick('width')}
                            />
                        </Group>
                    </Layer>
                </Stage>

                {/* Edit overlay */}
                {editingField && (
                    <div
                        className="absolute inset-0 bg-black/50 flex items-center justify-center z-10"
                        onClick={() => setEditingField(null)}
                    >
                        <div
                            className="bg-dark-800 rounded-xl p-6 shadow-xl border border-dark-600"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <h4 className="text-white font-semibold mb-4">
                                Edytuj {editingField === 'length' ? 'długość' : 'szerokość'}
                            </h4>
                            <div className="flex gap-3">
                                <input
                                    type="number"
                                    step="0.1"
                                    min="2"
                                    max="50"
                                    value={editValue}
                                    onChange={(e) => setEditValue(e.target.value)}
                                    onKeyDown={handleEditKeyDown}
                                    className="input-field w-32"
                                    autoFocus
                                />
                                <span className="flex items-center text-dark-400">m</span>
                                <button
                                    onClick={handleEditSubmit}
                                    className="btn-primary px-4"
                                >
                                    OK
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Quick info */}
            <div className="flex gap-4 text-sm">
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-brand-500" />
                    <span className="text-dark-400">Długość: <span className="text-white font-medium">{dimensions.length || 0} m</span></span>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded bg-success-500" />
                    <span className="text-dark-400">Szerokość: <span className="text-white font-medium">{dimensions.width || 0} m</span></span>
                </div>
                <div className="text-dark-400">
                    Powierzchnia: <span className="text-brand-400 font-medium">{realArea.toFixed(1)} m²</span>
                </div>
            </div>
        </div>
    );
}
