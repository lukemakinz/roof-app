import { create } from 'zustand';

export const useQuoteStore = create((set, get) => ({
    // Current quote being created/edited
    currentQuote: null,
    currentStep: 1,

    // For new quote wizard
    uploadedImage: null,
    dimensions: { length: 0, width: 0 },
    pitchAngle: 35,
    roofType: 'gable',
    obstacles: [],
    selectedMaterial: null,
    calculation: null,
    clientData: {
        client_name: '',
        client_email: '',
        client_phone: '',
        client_address: '',
    },

    // Actions
    setCurrentQuote: (quote) => set({ currentQuote: quote }),
    setCurrentStep: (step) => set({ currentStep: step }),
    nextStep: () => set((state) => ({ currentStep: Math.min(state.currentStep + 1, 6) })),
    prevStep: () => set((state) => ({ currentStep: Math.max(state.currentStep - 1, 1) })),

    setUploadedImage: (image) => set({ uploadedImage: image }),

    setDimensions: (dimensions) => set({ dimensions }),
    setPitchAngle: (pitchAngle) => set({ pitchAngle }),
    setRoofType: (roofType) => set({ roofType }),

    setObstacles: (obstacles) => set({ obstacles }),
    addObstacle: (type) => set((state) => {
        const existing = state.obstacles.find(o => o.type === type);
        if (existing) {
            return {
                obstacles: state.obstacles.map(o =>
                    o.type === type ? { ...o, quantity: o.quantity + 1 } : o
                ),
            };
        }
        return { obstacles: [...state.obstacles, { type, quantity: 1 }] };
    }),
    removeObstacle: (type) => set((state) => ({
        obstacles: state.obstacles
            .map(o => o.type === type ? { ...o, quantity: o.quantity - 1 } : o)
            .filter(o => o.quantity > 0),
    })),

    setSelectedMaterial: (material) => set({ selectedMaterial: material }),
    setCalculation: (calculation) => set({ calculation }),

    setClientData: (data) => set((state) => ({
        clientData: { ...state.clientData, ...data },
    })),

    // Reset wizard state
    resetWizard: () => set({
        currentQuote: null,
        currentStep: 1,
        uploadedImage: null,
        dimensions: { length: 0, width: 0 },
        pitchAngle: 35,
        roofType: 'gable',
        obstacles: [],
        selectedMaterial: null,
        calculation: null,
        clientData: {
            client_name: '',
            client_email: '',
            client_phone: '',
            client_address: '',
        },
    }),

    // Update from API response
    updateFromQuote: (quote) => set({
        currentQuote: quote,
        dimensions: quote.dimensions || { length: 0, width: 0 },
        pitchAngle: quote.pitch_angle || 35,
        roofType: quote.roof_type || 'gable',
        obstacles: quote.obstacles || [],
        selectedMaterial: quote.material,
        calculation: quote.materials_breakdown ? {
            plan_area: quote.plan_area,
            real_area: quote.real_area,
            materials: quote.materials_breakdown,
            summary: {
                materials_net: quote.total_net,
                total_gross: quote.total_gross,
            },
        } : null,
        clientData: {
            client_name: quote.client_name || '',
            client_email: quote.client_email || '',
            client_phone: quote.client_phone || '',
            client_address: quote.client_address || '',
        },
    }),
}));
