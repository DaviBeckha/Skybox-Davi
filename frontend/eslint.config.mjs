import { FlatCompat } from "@eslint/eslintrc";
import { dirname } from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // next-env.d.ts é gerado pelo `next build` e não deve ser editado/linted
    // (a referência de typed routes dispara @typescript-eslint/triple-slash-reference).
    ignores: [".next/**", "node_modules/**", "coverage/**", "next-env.d.ts"]
  }
];

export default eslintConfig;
