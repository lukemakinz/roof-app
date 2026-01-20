import { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { quotesAPI, materialsAPI } from '../lib/api';
import { useQuoteStore } from '../stores/quoteStore';
import Layout from '../components/Layout';
import ImageCanvas from '../components/ImageCanvas';
import toast from 'react-hot-toast';
import {
    Upload, Image, ArrowRight, ArrowLeft, Check, Loader2, AlertCircle,
    Home, Plus, Minus, FileText, Download, Send, RefreshCw
} from 'lucide-react';

const STEPS = [
    { id: 1, name: 'Upload', label: 'Zdjęcie' },
    { id: 2, name: 'Processing', label: 'Analiza AI' },
    { id: 3, name: 'Verification', label: 'Weryfikacja' },
    { id: 4, name: 'Material', label: 'Materiał' },
    { id: 5, name: 'Calculation', label: 'Kalkulacja' },
    { id: 6, name: 'Client', label: 'Oferta PDF' },
];

const ROOF_TYPES = [
    { value: 'gable', label: 'Dwuspadowy' },
    { value: 'hip', label: 'Kopertowy' },
    { value: 'mansard', label: 'Mansardowy' },
    { value: 'flat', label: 'Płaski' },
];

const PITCH_PRESETS = [
    { value: 25, label: 'Płaski (25°)' },
    { value: 35, label: 'Standard (35°)' },
    { value: 45, label: 'Stromy (45°)' },
];

export default function NewQuotePage() {
    const navigate = useNavigate();
    const { id } = useParams();
    const {
        currentQuote, currentStep, setCurrentQuote, setCurrentStep, nextStep, prevStep,
        dimensions, pitchAngle, roofType, obstacles, selectedMaterial, calculation, clientData,
        setDimensions, setPitchAngle, setRoofType, addObstacle, removeObstacle,
        setSelectedMaterial, setCalculation, setClientData, resetWizard, updateFromQuote,
    } = useQuoteStore();

    const [isLoading, setIsLoading] = useState(false);
    const [materials, setMaterials] = useState([]);
    const [uploadedFile, setUploadedFile] = useState(null);
    const [imageUrl, setImageUrl] = useState(null);

    // Fetch materials on mount
    useEffect(() => {
        materialsAPI.getAll().then((res) => {
            setMaterials(res.data.results || res.data);
        });
    }, []);

    // Load existing quote if editing
    useEffect(() => {
        if (id) {
            quotesAPI.getById(id).then((res) => {
                updateFromQuote(res.data);
                setImageUrl(res.data.original_image_url);
                if (res.data.ai_processed) {
                    setCurrentStep(3);
                }
            });
        } else {
            resetWizard();
        }
        return () => resetWizard();
    }, [id]);

    // Dropzone
    const onDrop = useCallback((acceptedFiles) => {
        const file = acceptedFiles[0];
        if (file) {
            setUploadedFile(file);
            setImageUrl(URL.createObjectURL(file));
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': ['.jpeg', '.jpg', '.png'], 'application/pdf': ['.pdf'] },
        maxSize: 10 * 1024 * 1024,
        multiple: false,
    });

    // Handlers
    const handleUploadAndProcess = async () => {
        if (!uploadedFile && !currentQuote?.original_image_url) {
            toast.error('Najpierw wybierz zdjęcie');
            return;
        }

        setIsLoading(true);
        try {
            let quoteId = currentQuote?.id;

            // Create quote if not exists
            if (!quoteId) {
                const createRes = await quotesAPI.create({});
                quoteId = createRes.data.id;
                setCurrentQuote(createRes.data);
            }

            // Ensure we have a valid quoteId
            if (!quoteId) {
                throw new Error('Nie udało się utworzyć wyceny');
            }

            // Upload image if new file
            if (uploadedFile) {
                await quotesAPI.uploadImage(quoteId, uploadedFile);
            }

            nextStep(); // Move to processing step

            // Start AI processing
            await quotesAPI.processAI(quoteId);

            // Get updated quote
            const quoteRes = await quotesAPI.getById(quoteId);
            updateFromQuote(quoteRes.data);
            setImageUrl(quoteRes.data.original_image_url);

            nextStep(); // Move to verification step
            toast.success('Analiza zakończona pomyślnie!');
        } catch (error) {
            console.error(error);
            toast.error(error.response?.data?.error || error.message || 'Wystąpił błąd podczas przetwarzania');
            setCurrentStep(1);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDimensionsUpdate = async () => {
        if (!currentQuote?.id) return;
        setIsLoading(true);
        try {
            await quotesAPI.updateDimensions(currentQuote.id, {
                length: dimensions.length,
                width: dimensions.width,
                pitch_angle: pitchAngle,
                roof_type: roofType,
            });
            await quotesAPI.updateObstacles(currentQuote.id, obstacles);
            nextStep();
        } catch (error) {
            toast.error('Błąd zapisu danych');
        } finally {
            setIsLoading(false);
        }
    };

    const handleCalculate = async () => {
        if (!selectedMaterial) {
            toast.error('Wybierz materiał');
            return;
        }
        setIsLoading(true);
        try {
            const res = await quotesAPI.calculate(currentQuote.id, selectedMaterial.id);
            setCalculation(res.data);
            updateFromQuote(res.data.quote);
            nextStep();
        } catch (error) {
            toast.error('Błąd kalkulacji');
        } finally {
            setIsLoading(false);
        }
    };

    const handleGeneratePDF = async () => {
        setIsLoading(true);
        try {
            await quotesAPI.update(currentQuote.id, clientData);
            const res = await quotesAPI.generatePDF(currentQuote.id, clientData);

            const quoteRes = await quotesAPI.getById(currentQuote.id);
            updateFromQuote(quoteRes.data);

            toast.success('PDF wygenerowany!');
        } catch (error) {
            toast.error('Błąd generowania PDF');
        } finally {
            setIsLoading(false);
        }
    };

    // Calculate plan and real area for display
    const planArea = dimensions.length * dimensions.width;
    const realArea = planArea / Math.cos((pitchAngle * Math.PI) / 180);

    return (
        <Layout>
            <div className="max-w-5xl mx-auto space-y-8 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-white">
                            {id ? 'Edycja wyceny' : 'Nowa wycena'}
                        </h1>
                        <p className="text-dark-400 mt-1">
                            {STEPS[currentStep - 1]?.label}
                        </p>
                    </div>
                    {currentQuote?.number && (
                        <div className="text-right">
                            <div className="text-dark-400 text-sm">Numer oferty</div>
                            <div className="text-white font-mono">{currentQuote.number}</div>
                        </div>
                    )}
                </div>

                {/* Steps indicator */}
                <div className="flex items-center justify-between">
                    {STEPS.map((step, idx) => (
                        <div key={step.id} className="flex items-center">
                            <div className="flex flex-col items-center">
                                <div
                                    className={`step-circle ${currentStep > step.id
                                        ? 'step-completed'
                                        : currentStep === step.id
                                            ? 'step-active'
                                            : 'step-pending'
                                        }`}
                                >
                                    {currentStep > step.id ? <Check className="w-5 h-5" /> : step.id}
                                </div>
                                <span className="text-xs text-dark-400 mt-2 hidden sm:block">{step.label}</span>
                            </div>
                            {idx < STEPS.length - 1 && (
                                <div
                                    className={`w-12 sm:w-24 h-0.5 mx-2 ${currentStep > step.id ? 'bg-success-500' : 'bg-dark-700'
                                        }`}
                                />
                            )}
                        </div>
                    ))}
                </div>

                {/* Step Content */}
                <div className="card min-h-[400px]">
                    {/* Step 1: Upload */}
                    {currentStep === 1 && (
                        <div className="space-y-6">
                            <div
                                {...getRootProps()}
                                className={`dropzone ${isDragActive ? 'dropzone-active' : ''}`}
                            >
                                <input {...getInputProps()} />
                                <div className="flex flex-col items-center">
                                    {imageUrl ? (
                                        <img src={imageUrl} alt="Preview" className="max-h-64 rounded-xl mb-4" />
                                    ) : (
                                        <>
                                            <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mb-4">
                                                <Upload className="w-8 h-8 text-brand-400" />
                                            </div>
                                            <h3 className="text-lg font-semibold text-white mb-2">
                                                Przeciągnij zdjęcie rzutu dachu
                                            </h3>
                                            <p className="text-dark-400 text-center">
                                                lub kliknij, aby wybrać plik<br />
                                                <span className="text-sm">JPEG, PNG, PDF • max 10 MB</span>
                                            </p>
                                        </>
                                    )}
                                </div>
                            </div>

                            <div className="flex justify-end">
                                <button
                                    onClick={handleUploadAndProcess}
                                    disabled={!uploadedFile && !currentQuote?.original_image_url}
                                    className="btn-primary flex items-center gap-2"
                                >
                                    {isLoading ? (
                                        <Loader2 className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <>
                                            Analizuj zdjęcie
                                            <ArrowRight className="w-5 h-5" />
                                        </>
                                    )}
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 2: Processing */}
                    {currentStep === 2 && (
                        <div className="flex flex-col items-center justify-center py-16">
                            <div className="relative">
                                <div className="w-24 h-24 rounded-full bg-brand-500/10 flex items-center justify-center">
                                    <RefreshCw className="w-12 h-12 text-brand-400 animate-spin" />
                                </div>
                                <div className="absolute inset-0 rounded-full border-4 border-brand-500/20 animate-pulse" />
                            </div>
                            <h3 className="text-xl font-semibold text-white mt-8">Analiza AI w toku...</h3>
                            <p className="text-dark-400 mt-2">Wykrywanie wymiarów i elementów dachu</p>
                            <div className="mt-8 space-y-2 text-sm text-dark-400">
                                <div className="flex items-center gap-2">
                                    <Check className="w-4 h-4 text-success-400" />
                                    Przetwarzanie obrazu
                                </div>
                                <div className="flex items-center gap-2">
                                    <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
                                    Analiza wymiarów...
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Verification */}
                    {currentStep === 3 && (
                        <div className="space-y-6">
                            <div className="grid lg:grid-cols-2 gap-6">
                                {/* Interactive Image Canvas */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="text-lg font-semibold text-white">Interaktywny podgląd</h3>
                                        <span className="text-sm text-dark-400 bg-dark-800 px-3 py-1 rounded-lg">
                                            AI Confidence: {Math.round((currentQuote?.ai_confidence || 0) * 100)}%
                                        </span>
                                    </div>
                                    {imageUrl && (
                                        <ImageCanvas
                                            imageUrl={imageUrl}
                                            dimensions={dimensions}
                                            onDimensionsChange={setDimensions}
                                            pitchAngle={pitchAngle}
                                        />
                                    )}
                                </div>

                                {/* Dimensions form */}
                                <div className="space-y-6">
                                    <h3 className="text-lg font-semibold text-white">Wymiary dachu</h3>

                                    <div className="grid grid-cols-2 gap-4">
                                        <div>
                                            <label className="label-text">Długość (m)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={dimensions.length}
                                                onChange={(e) => setDimensions({ ...dimensions, length: parseFloat(e.target.value) || 0 })}
                                                className="input-field"
                                            />
                                        </div>
                                        <div>
                                            <label className="label-text">Szerokość (m)</label>
                                            <input
                                                type="number"
                                                step="0.1"
                                                value={dimensions.width}
                                                onChange={(e) => setDimensions({ ...dimensions, width: parseFloat(e.target.value) || 0 })}
                                                className="input-field"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <label className="label-text">Typ dachu</label>
                                        <select
                                            value={roofType}
                                            onChange={(e) => setRoofType(e.target.value)}
                                            className="input-field"
                                        >
                                            {ROOF_TYPES.map((type) => (
                                                <option key={type.value} value={type.value}>{type.label}</option>
                                            ))}
                                        </select>
                                    </div>

                                    <div>
                                        <label className="label-text">Kąt nachylenia: {pitchAngle}°</label>
                                        <input
                                            type="range"
                                            min="15"
                                            max="60"
                                            value={pitchAngle}
                                            onChange={(e) => setPitchAngle(parseInt(e.target.value))}
                                            className="w-full accent-brand-500"
                                        />
                                        <div className="flex justify-between mt-2">
                                            {PITCH_PRESETS.map((preset) => (
                                                <button
                                                    key={preset.value}
                                                    onClick={() => setPitchAngle(preset.value)}
                                                    className={`text-xs px-3 py-1 rounded-lg transition-colors ${pitchAngle === preset.value
                                                        ? 'bg-brand-500 text-white'
                                                        : 'bg-dark-700 text-dark-300 hover:bg-dark-600'
                                                        }`}
                                                >
                                                    {preset.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    <div>
                                        <label className="label-text">Przeszkody</label>
                                        <div className="space-y-2">
                                            <div className="flex items-center justify-between p-3 bg-dark-800 rounded-xl">
                                                <span className="text-dark-200">Kominy</span>
                                                <div className="flex items-center gap-3">
                                                    <button onClick={() => removeObstacle('chimney')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Minus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                    <span className="w-8 text-center text-white font-medium">
                                                        {obstacles.find(o => o.type === 'chimney')?.quantity || 0}
                                                    </span>
                                                    <button onClick={() => addObstacle('chimney')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Plus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-dark-800 rounded-xl">
                                                <span className="text-dark-200">Okna dachowe</span>
                                                <div className="flex items-center gap-3">
                                                    <button onClick={() => removeObstacle('skylight')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Minus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                    <span className="w-8 text-center text-white font-medium">
                                                        {obstacles.find(o => o.type === 'skylight')?.quantity || 0}
                                                    </span>
                                                    <button onClick={() => addObstacle('skylight')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Plus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-dark-800 rounded-xl">
                                                <span className="text-dark-200">Wyłazy dachowe</span>
                                                <div className="flex items-center gap-3">
                                                    <button onClick={() => removeObstacle('roof_hatch')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Minus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                    <span className="w-8 text-center text-white font-medium">
                                                        {obstacles.find(o => o.type === 'roof_hatch')?.quantity || 0}
                                                    </span>
                                                    <button onClick={() => addObstacle('roof_hatch')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Plus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                </div>
                                            </div>
                                            <div className="flex items-center justify-between p-3 bg-dark-800 rounded-xl">
                                                <span className="text-dark-200">Kominki wentylacyjne</span>
                                                <div className="flex items-center gap-3">
                                                    <button onClick={() => removeObstacle('vent_pipe')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Minus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                    <span className="w-8 text-center text-white font-medium">
                                                        {obstacles.find(o => o.type === 'vent_pipe')?.quantity || 0}
                                                    </span>
                                                    <button onClick={() => addObstacle('vent_pipe')} className="p-1.5 bg-dark-700 rounded-lg hover:bg-dark-600">
                                                        <Plus className="w-4 h-4 text-dark-300" />
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="p-4 bg-brand-500/10 border border-brand-500/20 rounded-xl">
                                        <div className="flex justify-between text-sm">
                                            <span className="text-dark-300">Powierzchnia rzutu</span>
                                            <span className="text-white font-medium">{planArea.toFixed(1)} m²</span>
                                        </div>
                                        <div className="flex justify-between text-sm mt-2">
                                            <span className="text-dark-300">Powierzchnia rzeczywista</span>
                                            <span className="text-brand-400 font-semibold">{realArea.toFixed(1)} m²</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-between pt-4">
                                <button onClick={() => setCurrentStep(1)} className="btn-secondary flex items-center gap-2">
                                    <ArrowLeft className="w-5 h-5" />
                                    Wróć
                                </button>
                                <button onClick={handleDimensionsUpdate} disabled={isLoading} className="btn-primary flex items-center gap-2">
                                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Dalej'}
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 4: Material Selection */}
                    {currentStep === 4 && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-semibold text-white">Wybierz materiał pokryciowy</h3>

                            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                                {materials.map((material) => (
                                    <button
                                        key={material.id}
                                        onClick={() => setSelectedMaterial(material)}
                                        className={`card-hover text-left ${selectedMaterial?.id === material.id ? 'border-brand-500 shadow-glow' : ''
                                            }`}
                                    >
                                        <div className="flex items-start justify-between mb-3">
                                            <div className="text-dark-400 text-sm">{material.category_display}</div>
                                            {selectedMaterial?.id === material.id && (
                                                <div className="w-6 h-6 rounded-full bg-brand-500 flex items-center justify-center">
                                                    <Check className="w-4 h-4 text-white" />
                                                </div>
                                            )}
                                        </div>
                                        <h4 className="text-white font-semibold mb-2">{material.name}</h4>
                                        <p className="text-dark-400 text-sm mb-4 line-clamp-2">{material.description}</p>
                                        <div className="text-2xl font-bold text-brand-400">
                                            {parseFloat(material.price_per_m2).toFixed(0)} <span className="text-lg text-dark-400">PLN/m²</span>
                                        </div>
                                    </button>
                                ))}
                            </div>

                            {selectedMaterial && (
                                <div className="p-4 bg-dark-800 rounded-xl">
                                    <div className="flex justify-between items-center">
                                        <span className="text-dark-300">Szacunkowy koszt materiału:</span>
                                        <span className="text-xl font-bold text-white">
                                            ~{Math.round(realArea * parseFloat(selectedMaterial.price_per_m2) * 1.12).toLocaleString('pl-PL')} PLN
                                        </span>
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-between pt-4">
                                <button onClick={prevStep} className="btn-secondary flex items-center gap-2">
                                    <ArrowLeft className="w-5 h-5" />
                                    Wróć
                                </button>
                                <button onClick={handleCalculate} disabled={isLoading || !selectedMaterial} className="btn-primary flex items-center gap-2">
                                    {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Oblicz'}
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 5: Calculation Result */}
                    {currentStep === 5 && calculation && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-semibold text-white">Kalkulacja materiałów</h3>

                            <div className="grid sm:grid-cols-3 gap-4">
                                <div className="card bg-dark-800">
                                    <div className="text-dark-400 text-sm">Powierzchnia rzutu</div>
                                    <div className="text-2xl font-bold text-white mt-1">{calculation.plan_area} m²</div>
                                </div>
                                <div className="card bg-dark-800">
                                    <div className="text-dark-400 text-sm">Powierzchnia rzeczywista</div>
                                    <div className="text-2xl font-bold text-brand-400 mt-1">{calculation.real_area} m²</div>
                                </div>
                                <div className="card bg-dark-800">
                                    <div className="text-dark-400 text-sm">Z odpadem ({((selectedMaterial?.waste_factor || 1.12) - 1) * 100}%)</div>
                                    <div className="text-2xl font-bold text-white mt-1">
                                        {Math.round(calculation.real_area * (selectedMaterial?.waste_factor || 1.12))} m²
                                    </div>
                                </div>
                            </div>

                            <div className="card bg-dark-800 p-0 overflow-hidden">
                                <table className="w-full">
                                    <thead>
                                        <tr className="border-b border-dark-700">
                                            <th className="text-left text-dark-400 text-sm px-4 py-3">Materiał</th>
                                            <th className="text-right text-dark-400 text-sm px-4 py-3">Ilość</th>
                                            <th className="text-right text-dark-400 text-sm px-4 py-3">Wartość</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {Object.entries(calculation.materials).map(([key, item]) => (
                                            <tr key={key} className="border-b border-dark-700/50">
                                                <td className="px-4 py-3 text-white">{item.name}</td>
                                                <td className="px-4 py-3 text-right text-dark-300">{item.quantity} {item.unit}</td>
                                                <td className="px-4 py-3 text-right text-white font-medium">{item.total?.toLocaleString('pl-PL')} PLN</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <div className="card bg-gradient-to-r from-dark-800 to-dark-700 space-y-3">
                                <div className="flex justify-between">
                                    <span className="text-dark-300">Materiały netto</span>
                                    <span className="text-white">{calculation.summary.materials_net?.toLocaleString('pl-PL')} PLN</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-dark-300">Robocizna netto</span>
                                    <span className="text-white">{calculation.summary.labor_net?.toLocaleString('pl-PL')} PLN</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-dark-300">Razem netto</span>
                                    <span className="text-white font-medium">{calculation.summary.total_net?.toLocaleString('pl-PL')} PLN</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-dark-300">VAT {calculation.summary.vat_rate}%</span>
                                    <span className="text-white">{calculation.summary.vat?.toLocaleString('pl-PL')} PLN</span>
                                </div>
                                <div className="flex justify-between pt-3 border-t border-dark-600">
                                    <span className="text-lg font-semibold text-white">RAZEM BRUTTO</span>
                                    <span className="text-2xl font-bold text-brand-400">{calculation.summary.total_gross?.toLocaleString('pl-PL')} PLN</span>
                                </div>
                            </div>

                            <div className="flex justify-between pt-4">
                                <button onClick={prevStep} className="btn-secondary flex items-center gap-2">
                                    <ArrowLeft className="w-5 h-5" />
                                    Wróć
                                </button>
                                <button onClick={nextStep} className="btn-primary flex items-center gap-2">
                                    Generuj ofertę
                                    <ArrowRight className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 6: Client Data & PDF */}
                    {currentStep === 6 && (
                        <div className="space-y-6">
                            <h3 className="text-lg font-semibold text-white">Dane klienta i oferta PDF</h3>

                            <div className="grid lg:grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <div>
                                        <label className="label-text">Imię i nazwisko / Firma *</label>
                                        <input
                                            type="text"
                                            value={clientData.client_name}
                                            onChange={(e) => setClientData({ client_name: e.target.value })}
                                            className="input-field"
                                            placeholder="Jan Kowalski"
                                        />
                                    </div>
                                    <div>
                                        <label className="label-text">Email</label>
                                        <input
                                            type="email"
                                            value={clientData.client_email}
                                            onChange={(e) => setClientData({ client_email: e.target.value })}
                                            className="input-field"
                                            placeholder="jan@example.com"
                                        />
                                    </div>
                                    <div>
                                        <label className="label-text">Telefon</label>
                                        <input
                                            type="tel"
                                            value={clientData.client_phone}
                                            onChange={(e) => setClientData({ client_phone: e.target.value })}
                                            className="input-field"
                                            placeholder="+48 123 456 789"
                                        />
                                    </div>
                                    <div>
                                        <label className="label-text">Adres</label>
                                        <textarea
                                            value={clientData.client_address}
                                            onChange={(e) => setClientData({ client_address: e.target.value })}
                                            className="input-field min-h-[100px]"
                                            placeholder="ul. Przykładowa 123&#10;00-001 Warszawa"
                                        />
                                    </div>

                                    <button
                                        onClick={handleGeneratePDF}
                                        disabled={isLoading || !clientData.client_name}
                                        className="btn-primary w-full flex items-center justify-center gap-2"
                                    >
                                        {isLoading ? (
                                            <Loader2 className="w-5 h-5 animate-spin" />
                                        ) : (
                                            <>
                                                <FileText className="w-5 h-5" />
                                                Generuj PDF
                                            </>
                                        )}
                                    </button>
                                </div>

                                <div className="space-y-4">
                                    {currentQuote?.pdf_url ? (
                                        <div className="card border-success-500/20 bg-success-500/5">
                                            <div className="flex items-center gap-3 mb-4">
                                                <div className="w-12 h-12 rounded-xl bg-success-500/10 flex items-center justify-center">
                                                    <FileText className="w-6 h-6 text-success-400" />
                                                </div>
                                                <div>
                                                    <h4 className="text-white font-semibold">PDF gotowy!</h4>
                                                    <p className="text-dark-400 text-sm">Oferta {currentQuote.number}</p>
                                                </div>
                                            </div>
                                            <div className="flex gap-3">
                                                <a
                                                    href={currentQuote.pdf_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    className="btn-primary flex-1 flex items-center justify-center gap-2"
                                                >
                                                    <Download className="w-5 h-5" />
                                                    Pobierz
                                                </a>
                                                <button className="btn-secondary flex-1 flex items-center justify-center gap-2">
                                                    <Send className="w-5 h-5" />
                                                    Wyślij
                                                </button>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center py-12 text-center">
                                            <div className="w-16 h-16 rounded-2xl bg-dark-700 flex items-center justify-center mb-4">
                                                <FileText className="w-8 h-8 text-dark-400" />
                                            </div>
                                            <p className="text-dark-400">
                                                Wypełnij dane klienta i kliknij "Generuj PDF"
                                            </p>
                                        </div>
                                    )}

                                    <div className="card bg-dark-800">
                                        <h4 className="text-white font-medium mb-3">Podsumowanie</h4>
                                        <div className="space-y-2 text-sm">
                                            <div className="flex justify-between">
                                                <span className="text-dark-400">Materiał</span>
                                                <span className="text-white">{selectedMaterial?.name}</span>
                                            </div>
                                            <div className="flex justify-between">
                                                <span className="text-dark-400">Powierzchnia</span>
                                                <span className="text-white">{currentQuote?.real_area} m²</span>
                                            </div>
                                            <div className="flex justify-between pt-2 border-t border-dark-700">
                                                <span className="text-dark-300 font-medium">Wartość brutto</span>
                                                <span className="text-brand-400 font-bold">
                                                    {parseFloat(currentQuote?.total_gross || 0).toLocaleString('pl-PL')} PLN
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-between pt-4">
                                <button onClick={prevStep} className="btn-secondary flex items-center gap-2">
                                    <ArrowLeft className="w-5 h-5" />
                                    Wróć
                                </button>
                                <button onClick={() => navigate('/')} className="btn-ghost flex items-center gap-2">
                                    Zakończ
                                    <Home className="w-5 h-5" />
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
}
