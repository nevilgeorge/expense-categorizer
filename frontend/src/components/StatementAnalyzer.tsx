import { useState, useCallback } from 'react';
import { 
    Box, 
    Button, 
    Paper, 
    Typography, 
    CircularProgress,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
} from '@mui/material';
import { Upload as UploadIcon } from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import axios from 'axios';
import type { AnalysisResult, ApiError } from '../types';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'];

export const StatementAnalyzer = () => {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<AnalysisResult | null>(null);

    const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = event.target.files?.[0];
        if (selectedFile && selectedFile.type === 'application/pdf') {
            setFile(selectedFile);
            setError(null);
        } else {
            setError('Please select a PDF file');
            setFile(null);
        }
    };

    const handleUpload = useCallback(async () => {
        if (!file) return;

        setLoading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post<AnalysisResult>('http://127.0.0.1:8000/analyze-statement', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            setResult(response.data);
        } catch (err) {
            if (axios.isAxiosError(err)) {
                const errorData = err.response?.data as ApiError;
                setError(errorData?.detail || 'Failed to analyze statement');
            } else {
                setError('An unexpected error occurred');
            }
        } finally {
            setLoading(false);
        }
    }, [file]);

    const pieChartData = result ? Object.entries(result.spend_by_category).map(([name, value]) => ({
        name,
        value,
    })) : [];

    const paperStyle = {
        p: 3,
        mb: 3,
        width: '100%',
        backgroundColor: '#FFE2C3',
    };

    return (
        <Box 
            sx={{ 
                maxWidth: 780,
                mx: 'auto',
                p: 3,
                minHeight: '100vh',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'flex-start',
                width: '100%',
                overflowY: 'auto',
                position: 'relative',
            }}
        >
            <Box sx={{ width: '100%', py: 4 }}>
                <Paper sx={paperStyle}>
                    <Typography variant="h5" gutterBottom>
                        Upload a Chase credit card statement to see how you spend your money
                    </Typography>
                    
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                        <Button
                            variant="contained"
                            component="label"
                            startIcon={<UploadIcon />}
                            disabled={loading}
                        >
                            Select PDF
                            <input
                                type="file"
                                hidden
                                accept=".pdf"
                                onChange={handleFileChange}
                            />
                        </Button>
                        {file && (
                            <Typography variant="body2">
                                Selected: {file.name}
                            </Typography>
                        )}
                        <Button
                            variant="contained"
                            onClick={handleUpload}
                            disabled={!file || loading}
                        >
                            {loading ? <CircularProgress size={24} /> : 'Analyze'}
                        </Button>
                    </Box>

                    {error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                            {error}
                        </Alert>
                    )}
                </Paper>

                {result && (
                    <>
                        <Paper sx={paperStyle}>
                            <Typography variant="h6" gutterBottom>
                                Spending by Category
                            </Typography>
                            <Box sx={{ height: 400 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={pieChartData}
                                            dataKey="value"
                                            nameKey="name"
                                            cx="50%"
                                            cy="50%"
                                            outerRadius={150}
                                            label={({ name, percent }) => 
                                                `${name} (${(percent * 100).toFixed(1)}%)`
                                            }
                                        >
                                            {pieChartData.map((_, index) => (
                                                <Cell 
                                                    key={`cell-${index}`} 
                                                    fill={COLORS[index % COLORS.length]} 
                                                />
                                            ))}
                                        </Pie>
                                        <Tooltip 
                                            formatter={(value: number) => 
                                                `$${value.toFixed(2)}`
                                            }
                                        />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            </Box>
                        </Paper>

                        <Paper sx={{ ...paperStyle, mb: 0 }}>
                            <Typography variant="h6" gutterBottom>
                                Transactions
                            </Typography>
                            <TableContainer>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>Date</TableCell>
                                            <TableCell>Description</TableCell>
                                            <TableCell>Category</TableCell>
                                            <TableCell align="right">Amount</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {result.transactions.map((transaction, index) => (
                                            <TableRow key={index}>
                                                <TableCell>
                                                    {new Date(transaction.date).toLocaleDateString()}
                                                </TableCell>
                                                <TableCell>{transaction.description}</TableCell>
                                                <TableCell>{transaction.category}</TableCell>
                                                <TableCell align="right">
                                                    ${transaction.amount.toFixed(2)}
                                                </TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </Paper>
                    </>
                )}
            </Box>
        </Box>
    );
}; 