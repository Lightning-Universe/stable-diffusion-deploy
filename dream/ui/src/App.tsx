import {
  Box,
  Container,
  createTheme,
  CssBaseline,
  Grid,
  Link,
  ThemeProvider as MuiThemeProvider,
  ToggleButton,
  ToggleButtonGroup,
  useTheme,
} from '@mui/material';
import { Button, Stack, TextField } from 'lightning-ui/src/design-system/components';
import { theme } from 'lightning-ui/src/design-system/theme';
import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import DreamIcon from './assets/Dream.svg';
import FlashesIcon from './assets/Flashes.svg';
import LightningAIIcon from './assets/LightningAI.svg';
import LogoIcon from './assets/Logo.svg';
import SlackIcon from './assets/Slack.svg';
import SpeedIcon from './assets/Speed.svg';
import { ProgressBar } from './components/Loader';
import { AddYourSlackCredentials } from './components/SlackTokensModel';
import { Typography } from './components/Typography';
import { EULA } from './EULA';
import { useLightningState } from './hooks/useLightningState';
import { postDream } from './services/api';
import { LightingState } from './types/lightning';

const queryClient = new QueryClient();

type DreamProps = {
  dream: string;
  image: string | null;
};

enum Links {
  stableDiffusion = 'https://stability.ai/blog/stable-diffusion-public-release',
  runYouOwnVersion = 'https://lightning.ai/app/g1VJ8GZ7XF-AI-powered%20HackerNews', // todo: replace this with actual id from spreadsheet.
  slack = 'https://wsvbs-01gbz6hpp0nx2ahp49ect17q2n.litng-ai-03.litng.ai/slack/start',
  twitter = 'https://twitter.com/LightningAI',
  lightningAI = 'https://lightning.ai/',
  license = 'https://huggingface.co/spaces/CompVis/stable-diffusion-license',
}

function Dream({ dream, image }: DreamProps) {
  if (dream && !image) {
    return <ProgressBar />;
  }
  if (image) {
    return (
      <img src={image} alt={dream || ''} loading="lazy" style={{ maxWidth: '320px', width: '100%', height: 'auto' }} />
    );
  }
  return <></>;
}

function DreamSearch() {
  const { lightningState } = useLightningState();
  const [dream, setDream] = React.useState<string | null>('Cats in hats');
  const [result, setResult] = React.useState<string | null>(null);
  const [requestedDream, setRequestedDream] = React.useState('');

  const [view, setView] = useState<'speed' | 'hd'>('speed');
  const handleChange = (event: React.MouseEvent<HTMLElement>, nextView: 'speed' | 'hd') => {
    setView(nextView);
  };

  const [loading, setLoading] = useState(false);
  const dreamIt = async () => {
    if (dream && lightningState) {
      setResult(null);
      setRequestedDream(dream);
      setLoading(true);
      try {
        const result = await postDream(dream, view === 'hd', lightningState.vars.dream_url);
        setResult(result[0]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <Container maxWidth="sm">
      <Stack direction="column" justifyContent="center" alignItems="center" spacing={3} sx={{ marginTop: '16px' }}>
        <Stack direction="column" alignItems="center" spacing={1} textAlign={'center'}>
          <Box component={'div'} height={16} />
          <img src={LogoIcon} alt={'app-logo'} width={'90%'} />
          <Box component={'div'} height={{ xs: 16, sm: 0 }} />
          <Typography variant="subtitle1" color={(theme: any) => theme.palette.grey['70']}>
            Generate beautiful works of art in seconds!
          </Typography>
        </Stack>

        <Grid container spacing={1.5} justifyContent="center" alignItems="center" marginTop={'12px !important'}>
          <Grid item xs={12} marginBottom={{ xs: 1.5, sm: 0 }}>
            <ToggleButtonGroup exclusive fullWidth orientation={'horizontal'} value={view} onChange={handleChange}>
              <ToggleButton value="speed" aria-label="speed">
                <img src={SpeedIcon} alt={'app-logo'} />
                <Typography ml={1} fontSize={'14px'}>
                  Super speed
                </Typography>
              </ToggleButton>
              <ToggleButton value="hd" aria-label="hd" sx={{ svg: { color: 'red' } }}>
                <img src={FlashesIcon} alt={'app-logo'} />
                <Typography ml={1} fontSize={'14px'}>
                  High quality
                </Typography>
              </ToggleButton>
            </ToggleButtonGroup>
          </Grid>

          <Grid item xs={12}>
            <TextField value={dream} onChange={setDream} label={'Type in anything you can imagine'} fullWidth />
          </Grid>

          <Grid item xs={12} sx={{ '.MuiButton-root': { borderRadius: 40, padding: '0 30px' } }}>
            <Button
              disabled={!dream || loading}
              text="Dream it"
              onClick={dreamIt}
              fullWidth
              icon={<img src={DreamIcon} alt={'app-dream'} />}
            />
          </Grid>

          {requestedDream && (
            <Grid item xs={12} textAlign={'center'} my={1.5}>
              <Dream dream={requestedDream} image={result} />
            </Grid>
          )}

          <Grid item xs={12} textAlign={'center'}>
            <SlackOAuthLink />
            <Box component={'div'} height={23} />
          </Grid>
        </Grid>
      </Stack>
      {lightningState && <SlackFormAndLicense {...lightningState} />}
    </Container>
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
          MuiToggleButton: {
            styleOverrides: {
              root: {
                'border': 'none',
                'backgroundColor': '#E4E6EB',
                'img': {
                  color: 'red',
                },
                '&.Mui-selected': {
                  color: theme.palette.primary.main,
                  backgroundColor: theme.palette.primary['10'],
                },
                '&.Mui-selected:hover': {
                  color: theme.palette.primary.main,
                  backgroundColor: theme.palette.primary['20'],
                },
                '&.MuiToggleButtonGroup-grouped:not(:last-of-type)': {
                  borderRadius: '40px 4px 4px 40px',
                  marginRight: 1,
                },
                '&.MuiToggleButtonGroup-grouped:not(:first-of-type)': {
                  borderRadius: '4px 40px 40px 4px',
                  marginLeft: 1,
                },
              },
            },
          },
          MuiToggleButtonGroup: {
            defaultProps: {},
            styleOverrides: {
              root: {
                // marginTop: '0',
                height: '28px',
                minHeight: '100%',
              },
            },
          },
        },
      })}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <EULA>
            <DreamSearch />
          </EULA>
        </BrowserRouter>
      </QueryClientProvider>
    </MuiThemeProvider>
  );
}

export default App;

const SlackFormAndLicense = (lightningState: LightingState) => {
  const theme = useTheme();
  return (
    <Box
      component={'div'}
      sx={{
        textAlign: 'center',
        [theme.breakpoints.down('sm')]: { marginBottom: '50px', marginTop: '20px' },
        [theme.breakpoints.up('sm')]: { position: 'fixed', left: 0, right: 0, bottom: '30px' },
      }}>
      <AddYourSlackCredentials {...lightningState} />
      <br />

      <AppDetailsFooter />
    </Box>
  );
};

const AppDetailsFooter = () => (
  <Stack
    direction={{ xs: 'column', md: 'row' }}
    alignItems={'center'}
    justifyContent={'center'}
    rowGap={{ xs: 2, md: 0 }}>
    <Typography fontSize={'14px'} fontWeight={600}>
      Built with{' '}
      <Link href={Links.lightningAI} target={'_blank'} sx={{ position: 'relative', top: 4 }}>
        <img src={LightningAIIcon} alt={'LightningAI-logo'} />
      </Link>
    </Typography>
    <Typography color={'#C9CCD1'} fontWeight={200} display={{ xs: 'none', md: 'unset' }}>
      &nbsp;|&nbsp;
    </Typography>

    <Stack direction={'row'} alignItems={'center'} justifyContent={'center'}>
      <Typography fontSize={'14px'} color={theme => theme.palette.text.primary}>
        Powered by{' '}
        <Link href={Links.stableDiffusion} target={'_blank'}>
          Stable Diffusion
        </Link>
      </Typography>
      <Typography color={'#C9CCD1'} fontWeight={200}>
        &nbsp;|&nbsp;
      </Typography>
      <Typography fontSize={'14px'}>
        <Link href={Links.license} target={'_blank'}>
          License
        </Link>
      </Typography>
    </Stack>
  </Stack>
);

const SlackOAuthLink = () => {
  return (
    <Link
      href={Links.slack}
      target={'_blank'}
      rel="noreferrer"
      underline={'none'}
      sx={{ '.MuiButton-root': { borderRadius: 40 } }}>
      <Button text={'Add to slack'} icon={<img src={SlackIcon} alt={'app-dream'} />} color={'grey'} fullWidth />
    </Link>
  );
};
