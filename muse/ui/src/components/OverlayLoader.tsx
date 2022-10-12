import { Dialog, DialogContent, DialogTitle } from '@mui/material';
import { ProgressBar } from './ProgressBar';
import { Typography } from './Typography';

export const OverlayLoader = () => {
  return (
    <Dialog open={true}>
      <DialogTitle>Setting up servers to handle multiple requests</DialogTitle>
      <DialogContent>
        <Typography colorI="primary">This allows Muse to generate many images at the same time</Typography>
        <ProgressBar maxTime={10 * 60} />
      </DialogContent>
    </Dialog>
  );
};
