import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { StatementAnalyzer } from './components/StatementAnalyzer';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#CDD5C6',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#FBF2ED',
    },
  },
  typography: {
    fontFamily: '"Quicksand", "Helvetica", "Arial", sans-serif',
    h5: {
      fontWeight: 600,
      letterSpacing: '0.5px',
    },
    h6: {
      fontWeight: 500,
      letterSpacing: '0.3px',
    },
    body1: {
      fontWeight: 400,
    },
    body2: {
      fontWeight: 400,
    },
    button: {
      fontWeight: 600,
      textTransform: 'none',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#FBF2ED',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: '12px',
          padding: '8px 20px',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: '16px',
        },
      },
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <StatementAnalyzer />
    </ThemeProvider>
  );
}

export default App;
