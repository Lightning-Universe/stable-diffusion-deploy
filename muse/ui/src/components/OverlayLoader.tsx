import { Dialog, DialogContent, DialogTitle } from '@mui/material';
import { ProgressBar } from './ProgressBar';
import { Typography } from './Typography';

export const OverlayLoader = () => {
  return (
    <Dialog open={true}>
      <DialogTitle>Setting up load balancer</DialogTitle>
      <DialogContent>
        <Typography colorI="primary">This allows Muse to handle multiple requests</Typography>
        <ProgressBar maxTime={10 * 60} />
      </DialogContent>
    </Dialog>
  );
};
