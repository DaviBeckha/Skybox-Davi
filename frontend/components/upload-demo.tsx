"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { type ChangeEvent, type FormEvent, useRef, useState } from "react";

import { ApiError, api } from "@/lib/api";
import { queryKeys } from "@/lib/queries";

function describeError(error: unknown): string {
  if (error instanceof ApiError) {
    const body = error.body;
    if (body && typeof body === "object" && "detail" in body) {
      return String((body as Record<string, unknown>).detail);
    }
    return `Falha na importação (HTTP ${error.status}).`;
  }
  return "Não foi possível importar a demo. Verifique se o backend está no ar.";
}

export function UploadDemo() {
  const queryClient = useQueryClient();
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (selected: File) => api.importDemo(selected),
    onSuccess: () => {
      setFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      void queryClient.invalidateQueries({ queryKey: queryKeys.demos });
    }
  });

  function handleSelect(event: ChangeEvent<HTMLInputElement>) {
    const selected = event.target.files?.[0] ?? null;
    setValidationError(null);
    mutation.reset();
    if (selected && !selected.name.toLowerCase().endsWith(".dem")) {
      setFile(null);
      setValidationError("Selecione um arquivo .dem válido.");
      return;
    }
    setFile(selected);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setValidationError("Escolha um arquivo .dem antes de enviar.");
      return;
    }
    mutation.mutate(file);
  }

  const errorMessage = validationError ?? (mutation.isError ? describeError(mutation.error) : null);

  return (
    <form className="upload-form" onSubmit={handleSubmit} aria-label="Importar demo">
      <input
        ref={inputRef}
        id="demo-file"
        className="visually-hidden"
        type="file"
        accept=".dem"
        onChange={handleSelect}
      />
      <label className="button" htmlFor="demo-file">
        Escolher .dem
      </label>
      <span className="upload-filename">{file ? file.name : "Nenhum arquivo selecionado"}</span>
      <button className="button primary" type="submit" disabled={mutation.isPending}>
        {mutation.isPending ? "Enviando…" : "Importar demo"}
      </button>
      {errorMessage ? (
        <p className="form-error" role="alert">
          {errorMessage}
        </p>
      ) : null}
      {mutation.isSuccess ? (
        <p className="form-success">Demo importada e enfileirada para parsing.</p>
      ) : null}
    </form>
  );
}
