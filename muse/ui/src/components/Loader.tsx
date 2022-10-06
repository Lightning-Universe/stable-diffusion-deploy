import { Box, Typography } from '@mui/material';
import LinearProgress, { linearProgressClasses } from '@mui/material/LinearProgress';
import { styled } from '@mui/material/styles';
import { useCallback, useEffect, useState } from 'react';

export const ProgressBar = ({ maxTime = 60, title }: { maxTime?: number; title?: string }) => {
  const [time, setValue] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setValue(x => x + 1);
    }, 1000);
    return () => {
      clearInterval(timer);
    };
  }, []);

  const progressValue = useCallback(() => Math.round(time / (maxTime / 100)), [time, maxTime]);
  const hasReachedMaximum = useCallback(() => time >= maxTime, [time, maxTime]);

  return (
    <div>
      {maxTime > time && title && (
        <Typography fontFamily={'Roboto'} textAlign={'center'}>
          {title}
        </Typography>
      )}

      {/* 375 is iphone se, nothing is less than 300 fr */}
      <Box component={'div'} sx={{ width: '100%', minWidth: '300px' }} py={2}>
        <BorderLinearProgress
          variant={hasReachedMaximum() ? 'indeterminate' : 'determinate'}
          value={progressValue()}
          sx={{ marginBottom: '4px' }}
        />
        <Typography {...fontStyles.header} textAlign={'left'}>
          {hasReachedMaximum() ? `Taking longer than usual, try reloading the page` : `${progressValue()}%`}
          <span style={{ color: fontStyles.body.color }}>
            {!hasReachedMaximum() && ` - ${formatSeconds(maxTime - time)} left`}
          </span>
        </Typography>
      </Box>
    </div>
  );
};

const BorderLinearProgress = styled(LinearProgress)(({ theme }) => ({
  height: 8,
  borderRadius: 6,
  [`&.${linearProgressClasses.colorPrimary}`]: {
    backgroundColor: theme.palette.grey[theme.palette.mode === 'light' ? 200 : 800],
  },
  [`& .${linearProgressClasses.bar}`]: {
    borderRadius: 6,
    backgroundColor: theme.palette.primary['main'],
  },
}));

const formatSeconds = (seconds: number | undefined) => {
  if (!seconds) return '';
  const date = new Date(seconds * 1000);
  if (seconds <= 60) return `${date.getUTCSeconds()} seconds`;
  const minutes = date.getUTCMinutes();
  if (minutes > 1) return `${minutes} minutes and ${date.getUTCSeconds()} seconds`;
  return `1 minute and ${date.getUTCSeconds()} seconds`;
};

const fontStyles = {
  body: {
    fontFamily: 'Roboto',
    fontSize: '14px',
    fontWeight: 400,
    lineHeight: '20px',
    color: '#5B5E69',
  },
  header: {
    fontFamily: 'UCity',
    fontSize: '14px',
    fontWeight: 600,
    lineHeight: '20px',
    minWidth: '60px',
    color: '#1C1C1C',
  },
};
