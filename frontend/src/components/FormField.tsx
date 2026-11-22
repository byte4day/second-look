import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from 'react'
import { strings } from '../strings.ts'

interface FormFieldProps {
  id: string
  label: string
  error?: string
  children: ReactNode
}

export function FormField({ id, label, error, children }: FormFieldProps) {
  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      {children}
      {error ? (
        <p className="form-field__error" id={`${id}-error`} role="alert">
          {strings.problemPrefix}
          {error}
        </p>
      ) : null}
    </div>
  )
}

type InputProps = InputHTMLAttributes<HTMLInputElement> & { id: string }

export function TextInput({ id, className = '', ...rest }: InputProps) {
  return <input id={id} className={className} {...rest} />
}

type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement> & { id: string }

export function TextArea({ id, className = '', ...rest }: TextAreaProps) {
  return <textarea id={id} className={className} {...rest} />
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & { id: string }

export function SelectInput({ id, className = '', children, ...rest }: SelectProps) {
  return (
    <select id={id} className={className} {...rest}>
      {children}
    </select>
  )
}