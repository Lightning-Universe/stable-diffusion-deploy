import { ReactComponent as FlashesIcon } from './assets/Flashes.svg';
import LogoIcon from './assets/Logo.svg';
import MetaImage from './assets/header.png';
import { AppDetailsFooter, BuildYourAppBanner } from './components/FooterLinks';
import { ProgressBar } from './components/Loader';
import { AddYourSlackCredentials } from './components/SlackTokensModel';
import { Typography } from './components/Typography';
import { useLightningState } from './hooks/useLightningState';
import { postDream } from './services/api';
import { LightingState } from './types/lightning';
import CopyAllRoundedIcon from '@mui/icons-material/CopyAllRounded';
import {
  Box,
  Container,
  createTheme,
  CssBaseline,
  Grid,
  IconButton,
  IconButtonProps,
  OutlinedInput,
  StackProps,
  ThemeProvider as MuiThemeProvider,
} from '@mui/material';
import { Switch } from 'components/Switch';
import { getAndroidVersion } from 'hooks/usePlatform';
import { Button, Stack } from 'lightning-ui/src/design-system/components';
import { theme } from 'lightning-ui/src/design-system/theme';
import React, { useMemo, useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  image: string | null;
};

function Dream({ dream, image }: DreamProps) {
  if (dream && !image) return <ProgressBar />;

  if (!image)
    return (
      <Typography
        fontFamily={'Roboto'}
        sx={{
          textShadow: '0px 0px 6px rgba(255, 255, 255, 0.75)',
        }}>
        Your inspiration will appear here.
      </Typography>
    );

  return null;
}

function DreamSearch() {
  const androidVersion = useMemo(() => getAndroidVersion(), []);
  const { lightningState } = useLightningState();
  const [dream, setDream] = React.useState<string | null>('woman painting a large red egg in a dali landscape');
  const [result, setResult] = React.useState<string | null>(MetaImage);
  const [requestedDream, setRequestedDream] = React.useState('');
  const [fastGen, setFastGen] = useState(true);

  const [loading, setLoading] = useState(false);
  const dreamIt = async () => {
    if (dream && lightningState) {
      setResult(null);
      setRequestedDream(dream);
      setLoading(true);
      try {
        const result = await postDream(dream, fastGen === false, lightningState.vars.dream_url);
        setResult(result);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div>
      <Box sx={{ position: 'sticky', left: 0, right: 0, top: 0, zIndex: 10 }}>
        <BuildYourAppBanner />
      </Box>
      <Grid
        container
        justifyContent="center"
        alignItems="stretch"
        sx={{ paddingBottom: 10 }}
        direction={{
          xs: 'row',
          md: 'row-reverse',
        }}>
        {/* app logo and details */}
        <Grid item xs={12}>
          <AppAbout display={{ md: 'none' }} />
        </Grid>

        {/* image generation */}
        <Grid item xs={12} sm={12} md={7} lg={8} xl={7} textAlign={'center'} sx={{ position: 'relative' }}>
          <Box
            sx={{
              display: androidVersion === 0 ? 'block' : 'none',
              position: 'absolute',
              top: '12px',
              right: '12px',
              zIndex: 8,
              background: '#FFFFFFBF',
              borderRadius: 40,
            }}>
            <DownloadImageButton disabled={!result} onClick={() => result && copyImageToClipboard(result)} />
          </Box>
          <Box
            sx={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '80%' }}>
            <Dream dream={requestedDream} image={result} />
          </Box>
          <img
            src={result ?? MetaImage}
            loading="lazy"
            alt={'bg'}
            style={{ opacity: result ? 1 : 0.25 }}
            width={'100%'}
          />
        </Grid>

        {/* controls */}
        <Grid item xs={12} sm={12} md={5} lg={4} xl={5} paddingX={2}>
          {/* maxWidth={'500px !important'} */}
          <AppAbout display={{ xs: 'none', md: 'block' }} paddingBottom={6} paddingTop={6} />
          <Box height={16} />
          <Container maxWidth={'sm'} disableGutters>
            <OutlinedInput
              multiline
              value={dream}
              onChange={e => setDream(e.target.value)}
              placeholder={'Type in anything you can imagine'}
              fullWidth
              inputProps={{
                enterkeyhint: 'go',
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
                  <Switch checked={fastGen} onChange={e => setFastGen(e.target.checked)} />
                </Box>
                <Typography colorI={'primary'} fontFamily={'Roboto'} variant={'body2'}>
                  {fastGen ? 'Fast' : 'More creative (slower)'}
                </Typography>
              </Row>

              <Box sx={{ '.MuiButton-root': { borderRadius: 40 } }}>
                <Button disabled={!dream || loading} text="Muse" onClick={dreamIt} fullWidth icon={<FlashesIcon />} />
              </Box>
            </Row>
          </Container>
        </Grid>
      </Grid>

      {lightningState && <SlackFormAndLicense {...lightningState} />}
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
        <BrowserRouter>
          <DreamSearch />
        </BrowserRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

export default App;

const SlackFormAndLicense = (lightningState: LightingState) => {
  return (
    <Box
      sx={{
        background: '#fff',
        textAlign: 'center',
        position: 'fixed',
        left: 0,
        right: 0,
        bottom: 0,
        paddingBottom: 1.5,
      }}>
      <AddYourSlackCredentials {...lightningState} />
      <Box height={8} />
      <Grid container>
        <Grid item xs={12} sm={12} md={5} lg={4} xl={5} paddingX={2}>
          <AppDetailsFooter />
        </Grid>
      </Grid>
    </Box>
  );
};

const Row = (props: StackProps) => {
  return <Stack display={'flex'} flexDirection={'row'} alignItems={'center'} {...props} />;
};

const AppAbout = (props: Pick<StackProps, 'display' | 'paddingBottom' | 'paddingTop'>) => (
  <Stack direction="column" alignItems={'center'} spacing={1} textAlign={'center'} {...props}>
    <Box height={{ xs: 8, sm: 16 }} />
    <img src={LogoIcon} alt={'app-logo'} height={52} />
    <Typography variant="subtitle1" color={(theme: any) => theme.palette.grey['70']}>
      Use AI to inspire your art
    </Typography>
  </Stack>
);

const DownloadImageButton = (props: IconButtonProps) => {
  return (
    <IconButton {...props}>
      <CopyAllRoundedIcon style={{ color: '#1C1C1C' }} />
    </IconButton>
  );
};

const copyImageToClipboard = async (content: string) => {
  const blobToClipboard = (content: string | Promise<Blob> | Blob) => {
    try {
      navigator.clipboard.write([new ClipboardItem({ 'image/png': content })]);
    } catch (e) {
      console.warn(e);
    }
  };

  // todo: add better error handler
  if (content.startsWith('/static')) {
    const imgContent = await (await fetch(content)).blob();
    blobToClipboard(imgContent);
    return;
  }
  blobToClipboard(content);
};
