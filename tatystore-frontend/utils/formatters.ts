// utils/formatters.ts

/**
 * Aplica a máscara de CPF (###.###.###-##) a uma string.
 * @param value A string a ser formatada.
 * @returns A string com a máscara de CPF.
 */
export const maskCPF = (value: string): string => {
  if (!value) return "";
  return value
    .replace(/\D/g, '') // Remove todos os caracteres não numéricos
    .slice(0, 11) // Limita a 11 dígitos
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d)/, '$1.$2')
    .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
};

/**
 * Aplica a máscara de telefone ((##) #####-#### ou (##) ####-####) a uma string.
 * @param value A string a ser formatada.
 * @returns A string com a máscara de telefone.
 */
export const maskPhone = (value: string): string => {
  if (!value) return "";
  const cleaned = value.replace(/\D/g, '').slice(0, 11);
  if (cleaned.length <= 10) {
    return cleaned
      .replace(/(\d{2})(\d)/, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  }
  return cleaned
    .replace(/(\d{2})(\d)/, '($1) $2')
    .replace(/(\d{5})(\d)/, '$1-$2');
};

/**
 * Aplica a máscara de CNPJ (##.###.###/####-##) a uma string.
 * @param value A string a ser formatada.
 * @returns A string com a máscara de CNPJ.
 */
export const maskCNPJ = (value: string): string => {
  if (!value) return "";
  return value
    .replace(/\D/g, '') // Remove todos os caracteres não numéricos
    .slice(0, 14) // Limita a 14 dígitos
    .replace(/(\d{2})(\d)/, '$1.$2')
    .replace(/(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2');
};

/**
 * Valida se uma string é um e-mail válido.
 * @param email O e-mail a ser validado.
 * @returns `true` se o e-mail for válido, `false` caso contrário.
 */
export const validateEmail = (email: string): boolean => {
    if (!email) return false;
    const re = /^\S+@\S+\.\S+$/;
    return re.test(String(email).toLowerCase());
};

/**
 * Remove todos os caracteres não numéricos de uma string.
 * @param value A string a ser limpa.
 * @returns Uma string contendo apenas os dígitos.
 */
export const unmask = (value: string): string => {
    if (!value) return "";
    return value.replace(/\D/g, '');
};
