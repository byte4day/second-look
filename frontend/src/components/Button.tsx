import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'danger'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  block?: boolean
  children: ReactNode
  to?: never
}

interface LinkButtonProps {
  variant?: Variant
  block?: boolean
  children: ReactNode
  href: string
  className?: string
}

const variantClass: Record<Variant, string> = {
  primary: 'btn btn--primary',
  secondary: 'btn btn--secondary',
  danger: 'btn btn--danger',
}

export function Button({
  variant = 'secondary',
  block,
  className = '',
  children,
  type = 'button',
  ...rest
}: ButtonProps) {
  const classes = [
    variantClass[variant],
    block ? 'btn--block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return (
    <button type={type} className={classes} {...rest}>
      {children}
    </button>
  )
}

export function LinkButton({
  variant = 'secondary',
  block,
  href,
  className = '',
  children,
}: LinkButtonProps) {
  const classes = [
    variantClass[variant],
    block ? 'btn--block' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return (
    <a className={classes} href={href}>
      {children}
    </a>
  )
}