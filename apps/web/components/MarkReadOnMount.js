"use client";

import { useEffect } from "react";
import { markRead } from "@/lib/api";

export default function MarkReadOnMount({ id }) {
  useEffect(() => {
    markRead(id).catch(() => {});
  }, [id]);
  return null;
}
