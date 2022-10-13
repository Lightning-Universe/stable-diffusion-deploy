import {
  Box,
  Container,
  createTheme,
  CssBaseline,
  Grid,
  OutlinedInput,
  StackProps,
  ThemeProvider as MuiThemeProvider,
} from '@mui/material';
import { DownloadImageButton } from 'components/DownloadImageButton';
import { Switch } from 'components/Switch';
import { Button, SnackbarProvider, Stack, useSnackbar } from 'lightning-ui/src/design-system/components';
import { theme } from 'lightning-ui/src/design-system/theme';
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { ReactComponent as FlashesIcon } from './assets/Flashes.svg';
import MetaImage from './assets/header.png';
import LogoIcon from './assets/Logo.svg';
import { BuildYourAppBanner } from './components/BuildYourAppBanner';
import { Footer } from './components/Footer';
import { OverlayLoader } from './components/OverlayLoader';
import { ProgressBar } from './components/ProgressBar';
import { Typography } from './components/Typography';
import { useLightningState } from './hooks/useLightningState';
import { postDream } from './services/api';
import { LightingState } from './types/lightning';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  loading: boolean;
  image: string | null;
  maxTime?: number;
};

function Dream({ loading, dream, image, maxTime }: DreamProps) {
  if (image) return null;

  if (dream && loading) return <ProgressBar maxTime={maxTime} title={'Finding inspiration...'} />;

  return (
    <Typography
      fontFamily={'Roboto'}
      textAlign={'center'}
      sx={{
        textShadow: '0px 0px 6px rgba(255, 255, 255, 0.75)',
      }}>
      Your inspiration will appear here
    </Typography>
  );
}

function DreamSearch() {
  const { lightningState } = useLightningState();

  const { enqueueSnackbar } = useSnackbar();
  const [query, setQuery] = React.useState<string>('Woman painting a large red egg in a dali landscape');
  const [loading, setLoading] = useState(false);
  const [imgResult, setImgResult] = React.useState<string | null>(null);
  const [placeHolderImage, setPlaceholderImage] = useState(MetaImage);

  const [highQuality, setHighQuality] = useState(false);
  const [requestedDream, setRequestedDream] = React.useState('');

  const dreamIt = async () => {
    if (query && lightningState && !loading) {
      if (imgResult) setPlaceholderImage(imgResult);
      setImgResult(null);
      setRequestedDream(query);
      setLoading(true);
      try {
        const result = await postDream(query, highQuality, lightningState.vars.dream_url);
        setImgResult(result.image);
      } catch {
        enqueueSnackbar({
          title: 'Failed to query please try again',
          severity: 'error',
        });
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div>
      {!lightningState?.vars?.dream_url && <OverlayLoader />}

      <Box sx={{ position: 'sticky', left: 0, right: 0, top: 0, zIndex: 10 }}>
        <BuildYourAppBanner />
      </Box>
      <Grid
        container
        justifyContent={{ xs: 'center', lg: 'flex-start' }}
        alignItems="stretch"
        direction={{ xs: 'row', md: 'row-reverse' }}>
        {/* app logo and details */}
        <Grid item xs={12}>
          <AppAbout display={{ lg: 'none' }} />
        </Grid>

        {/* image generation */}
        <Grid item xs={12} md={'auto'} position={'relative'} maxWidth={'100% !important'}>
          <DownloadImageButton imgResult={imgResult} query={query} />
          <Box
            sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '80%' }}>
            <Dream loading={loading} dream={requestedDream} image={imgResult} maxTime={highQuality ? 120 : 60} />
          </Box>
          <Box
            sx={{
              '>img': {
                xs: { width: '100% !important' },
                md: { width: 'auto !important', height: 'calc(100vh - 40px - 52px )' },
              },
            }}>
            <img
              id={'imgResult'}
              src={imgResult ?? placeHolderImage}
              loading="lazy"
              alt={'bg'}
              style={{
                maxWidth: '100%',
                aspectRatio: '1 / 1',
                opacity: imgResult ? 1 : 0.25,
                filter: imgResult ? 'none' : 'saturate(0)',
              }}
            />
          </Box>
        </Grid>

        {/* controls */}
        <Grid item xs={12} md={'auto'} paddingX={1} sx={{ flexGrow: '1 !important' }}>
          <Box sx={{ minWidth: '300px' }}>
            <AppAbout display={{ xs: 'none', lg: 'block' }} paddingBottom={6} paddingTop={6} />
            <Box height={16} />
            <Container maxWidth={'sm'} disableGutters>
              <OutlinedInput
                multiline
                value={query}
                onChange={e => setQuery(e.target.value)}
                placeholder={'Type in anything you can imagine'}
                fullWidth
                inputProps={{
                  enterKeyHint: 'go',
                  onKeyDown: ev => {
                    if (ev.key === 'Enter' && !ev.shiftKey) {
                      ev.preventDefault();
                      dreamIt();
                      ev.currentTarget.blur();
                      window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                  },
                }}
              />
              <Box height={16} />
              <Row sx={{ 'justifyContent': 'space-between', '>div': { width: '100%' } }}>
                <Row>
                  <Box mr={1}>
                    <Switch checked={!highQuality} onChange={() => setHighQuality(x => !x)} disabled={loading} />
                  </Box>
                  <Typography colorI={'primary'} fontFamily={'Roboto'} variant={'body2'}>
                    {highQuality ? 'High quality (slower)' : 'Fast'}
                  </Typography>
                </Row>

                <Box sx={{ '.MuiButton-root': { borderRadius: 40 } }}>
                  <Button
                    disabled={!query || loading || !lightningState?.vars?.dream_url}
                    text="Muse"
                    onClick={dreamIt}
                    fullWidth
                    icon={<FlashesIcon />}
                  />
                </Box>
              </Row>
              <Box height={8} />
            </Container>
          </Box>
        </Grid>
      </Grid>
      <Box height={{ xs: 0, md: 80, lg: 0 }} />
      {lightningState && <FooterWithLicense {...lightningState} />}
    </div>
  );
}

function App() {
  return (
    <MuiThemeProvider
      theme={createTheme({
        ...theme,
        shape: {
          borderRadius: 8,
        },
        components: {
          ...theme.components,
          MuiLink: {
            defaultProps: { underline: 'none' },
          },
          MuiOutlinedInput: {
            defaultProps: {
              sx: {
                'fontFamily': 'Roboto',
                'fontStyle': 'normal',
                'fontWeight': 'normal',
                'fontSize': '14px',
                'padding': '8px 12px',
                'backgroundColor': 'white',
                'borderRadius': '26px',
                '&.MuiInputBase-colorPrimary:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: (theme: any) => theme.palette['primary'].main,
                },
                '&.Mui-error .MuiOutlinedInput-notchedOutline': {
                  padding: 0,
                },
              },
            },
          },
        },
      })}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <SnackbarProvider>
          <BrowserRouter>
            <DreamSearch />
          </BrowserRouter>
        </SnackbarProvider>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

export default App;

const FooterWithLicense = (lightningState: LightingState) => {
  return (
    <>
      <Box
        position={{ xs: 'initial', md: 'fixed' }}
        sx={{
          'background': '#FFFFFF',
          'textAlign': 'center',
          'left': 0,
          'right': 0,
          'bottom': 0,
          '>div': {
            paddingBottom: { md: 1.5, xs: 8 },
            paddingTop: { md: 2, xs: 4 },
            boxShadow: {
              xs: 'none',
              md: '0px -3px 1px -2px rgb(45 64 86 / 20%);',
            },
          },
        }}>
        <Footer apiLink={(lightningState?.flows?.api_component?.vars?._layout as any)?.target} />
      </Box>
      <Box
        position={{ xs: 'fixed' }}
        display={{ md: 'none' }}
        sx={{
          height: 56,
          background: '#FFFFFF',
          textAlign: 'center',
          left: 0,
          right: 0,
          bottom: 0,
          boxShadow: {
            xs: '0px -3px 1px -2px rgb(45 64 86 / 20%);',
          },
        }}
      />
    </>
  );
};

const Row = (props: StackProps) => {
  return <Stack display={'flex'} flexDirection={'row'} alignItems={'center'} {...props} />;
};

const AppAbout = (props: Pick<StackProps, 'display' | 'paddingBottom' | 'paddingTop'>) => (
  <Stack direction="column" alignItems={'center'} spacing={1} textAlign={'center'} {...props}>
    <Box height={{ xs: 16, sm: 16 }} />
    <Box sx={{ img: { height: { xs: 52, sm: 70, md: 80 } } }}>
      <img src={LogoIcon} alt={'app-logo'} />
    </Box>
    <Typography
      variant="subtitle1"
      color={(theme: any) => theme.palette.grey['70']}
      marginTop={{ xs: '0 !important' }}>
      Use AI to inspire your art
    </Typography>
    <Box height={{ xs: 8 }} />
  </Stack>
);
