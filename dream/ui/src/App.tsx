import { CircularProgress, Container, Grid, Typography } from '@mui/material';
import { useLightningState } from 'hooks/useLightningState';
import { Button, OutlinedInput, SnackbarProvider, Stack } from 'lightning-ui/src/design-system/components';
import ThemeProvider from 'lightning-ui/src/design-system/theme';
import React from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { postDream } from './services/api';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  image: string | null;
};

function Dream({ dream, image }: DreamProps) {
  if (dream && !image) {
    return <CircularProgress />;
  }
  if (image) {
    return <img src={image} alt={dream || ''} loading="lazy" width="256px" height="256px" />;
  }
  return <></>;
}

function DreamSearch() {
  const { lightningState } = useLightningState();
  const [dream, setDream] = React.useState<string | null>('');
  const [result, setResult] = React.useState<string | null>(null);
  const [requestedDream, setRequestedDream] = React.useState('');

  const dreamIt = async () => {
    if (dream && lightningState) {
      setResult(null);
      setRequestedDream(dream);
      const result = await postDream(dream, 1, 512, lightningState.vars.dream_url);
      console.log(result);
      setResult(result['data'][0]);
    }
  };

  return (
    <Container maxWidth="sm">
      <Stack direction="column" justifyContent="center" alignItems="center" spacing={3} sx={{ marginTop: '16px' }}>
        <Stack direction="column" alignItems="center" spacing={1}>
          <Typography variant="h4" align="center">
            Lightning Dream Generator
          </Typography>
          <Typography variant="subtitle1">Powered by Stable Diffusion</Typography>
        </Stack>
        <Grid container spacing={1} justifyContent="center" alignItems="center">
          <Grid item xs={12} md>
            <OutlinedInput
              fullWidth
              onChange={event => setDream(event.target.value)}
              placeholder="Cats in hats"
              sx={{
                'fontFamily': 'Roboto',
                'fontStyle': 'normal',
                'fontWeight': 'normal',
                'fontSize': '14px',
                'lineHeight': '20px',
                'height': '36px',
                'backgroundColor': 'white',
                'borderRadius': '6px',
                '&.MuiInputBase-colorPrimary:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: (theme: any) => theme.palette['primary'].main,
                },
                '&.Mui-error .MuiOutlinedInput-notchedOutline': {
                  padding: 0,
                },
                '&.Mui-disabled': {
                  backgroundColor: (theme: any) => theme.palette.grey['10'],
                },
                '&.Mui-disabled:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(0,0,0,0.26)',
                },
                '&.Mui-error.Mui-disabled .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(0,0,0,0.26)',
                },
                '&.Mui-disabled .MuiOutlinedInput-input': {
                  color: (theme: any) => theme.palette.grey['20'],
                },
                '&.MuiInputBase-sizeSmall': {
                  height: '28px',
                },
              }}
            />
          </Grid>
          <Grid item>
            <Button disabled={!dream} text="Dream it" onClick={dreamIt} />
          </Grid>
        </Grid>
        {requestedDream && <Dream dream={requestedDream} image={result} />}
      </Stack>
    </Container>
  );
}

function App() {
  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <SnackbarProvider>
            <DreamSearch />
          </SnackbarProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  );
}

export default App;
