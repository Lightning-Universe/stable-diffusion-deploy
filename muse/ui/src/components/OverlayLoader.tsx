import { Dialog, DialogContent, DialogTitle } from '@mui/material';
import { ProgressBar } from './Loader';

export const OverlayLoader = () => {
  return (
    <Dialog open={true}>
      <DialogTitle>Muse is getting ready...</DialogTitle>
      <DialogContent>
        <ProgressBar maxTime={10 * 60} />
      </DialogContent>
    </Dialog>
  );
};
