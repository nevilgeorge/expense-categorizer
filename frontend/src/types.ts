export interface Transaction {
    date: string;
    description: string;
    amount: number;
    category: string;
}

export interface AnalysisResult {
    transactions: Transaction[];
    spend_by_category: Record<string, number>;
}

export interface ApiError {
    detail: string;
} 