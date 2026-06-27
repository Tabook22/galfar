import { useCallback, useRef, useState } from "react";

interface ConfirmOptions {
  title?: string;
}

export function useConfirmDialog() {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [title, setTitle] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);
  const actionRef = useRef<(() => Promise<void>) | null>(null);

  const requestConfirm = useCallback(
    (msg: string, action: () => Promise<void>, options?: ConfirmOptions) => {
      setMessage(msg);
      setTitle(options?.title);
      actionRef.current = action;
      setOpen(true);
    },
    []
  );

  const cancel = useCallback(() => {
    if (loading) return;
    setOpen(false);
    actionRef.current = null;
  }, [loading]);

  const confirm = useCallback(async () => {
    const action = actionRef.current;
    if (!action) return;
    setLoading(true);
    try {
      await action();
      setOpen(false);
      actionRef.current = null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { open, message, title, loading, requestConfirm, cancel, confirm };
}
