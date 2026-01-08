import { type FC } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle
} from '@/components/ui/dialog'

interface DeleteSessionModalProps {
  isOpen: boolean
  onClose: () => void
  onDelete: () => Promise<void>
  isDeleting: boolean
}

const DeleteSessionModal: FC<DeleteSessionModalProps> = ({
  isOpen,
  onClose,
  onDelete,
  isDeleting
}) => (
  <Dialog open={isOpen} onOpenChange={onClose}>
    <DialogContent className="border-gray-300 bg-light-surface font-geist dark:border-gray-700 dark:bg-dark-surface">
      <DialogHeader>
        <DialogTitle className="text-light-text dark:text-dark-text">Confirm deletion</DialogTitle>
        <DialogDescription className="text-light-text-secondary dark:text-dark-text-secondary">
          This will permanently delete the session. This action cannot be
          undone.
        </DialogDescription>
      </DialogHeader>
      <DialogFooter>
        <Button
          variant="outline"
          className="rounded-xl border-gray-300 font-geist text-light-text hover:bg-light-bg dark:border-gray-700 dark:text-dark-text dark:hover:bg-dark-bg"
          onClick={onClose}
          disabled={isDeleting}
        >
          CANCEL
        </Button>
        <Button
          variant="destructive"
          onClick={onDelete}
          disabled={isDeleting}
          className="rounded-xl font-geist"
        >
          DELETE
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
)

export default DeleteSessionModal
