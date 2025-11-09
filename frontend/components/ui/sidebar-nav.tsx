"use client";

import { cn } from "@/lib/utils";
import Link, { LinkProps } from "next/link";
import React, { useState, createContext, useContext } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Menu, X } from "lucide-react";

interface Links {
  label: string;
  href: string;
  icon: React.JSX.Element | React.ReactNode;
}

interface SidebarContextProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  animate: boolean;
}

const SidebarContext = createContext<SidebarContextProps | undefined>(
  undefined
);

export const useSidebar = () => {
  const context = useContext(SidebarContext);
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider");
  }
  return context;
};

export const SidebarProvider = ({
  children,
  open: openProp,
  setOpen: setOpenProp,
  animate = true,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  const [openState, setOpenState] = useState(false);

  const open = openProp !== undefined ? openProp : openState;
  const setOpen = setOpenProp !== undefined ? setOpenProp : setOpenState;

  return (
    <SidebarContext.Provider value={{ open, setOpen, animate }}>
      {children}
    </SidebarContext.Provider>
  );
};

export const Sidebar = ({
  children,
  open,
  setOpen,
  animate,
}: {
  children: React.ReactNode;
  open?: boolean;
  setOpen?: React.Dispatch<React.SetStateAction<boolean>>;
  animate?: boolean;
}) => {
  return (
    <SidebarProvider open={open} setOpen={setOpen} animate={animate}>
      {children}
    </SidebarProvider>
  );
};

export const SidebarBody = (props: React.ComponentProps<typeof motion.div>) => {
  return (
    <>
      <DesktopSidebar {...props} />
      <MobileSidebar {...(props as React.ComponentProps<"div">)} />
    </>
  );
};

export const DesktopSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<typeof motion.div>) => {
  const { open, setOpen, animate } = useSidebar();
  return (
    <motion.div
      className={cn(
        "h-screen px-0 py-2 hidden md:flex md:flex-col bg-[hsl(var(--tv-surface))] w-[48px] flex-shrink-0 fixed left-0 top-0 z-40 overflow-y-auto border-r border-[hsl(var(--tv-border))]",
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const MobileSidebar = ({
  className,
  children,
  ...props
}: React.ComponentProps<"div">) => {
  const { open, setOpen } = useSidebar();
  return (
    <>
      <div
        className={cn(
          "h-12 px-4 py-2 flex flex-row md:hidden items-center justify-between bg-[hsl(var(--tv-surface))] w-full fixed top-0 left-0 right-0 z-50 border-b border-[hsl(var(--tv-border))]"
        )}
        {...props}
      >
        <div className="flex justify-end z-20 w-full">
          <Menu
            className="text-[hsl(var(--tv-text-primary))] cursor-pointer"
            onClick={() => setOpen(!open)}
          />
        </div>
        <AnimatePresence>
          {open && (
            <motion.div
              initial={{ x: "-100%", opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: "-100%", opacity: 0 }}
              transition={{
                duration: 0.3,
                ease: "easeInOut",
              }}
              className={cn(
                "fixed h-full w-full inset-0 bg-[hsl(var(--tv-background))] p-10 z-[100] flex flex-col justify-between overflow-y-auto",
                className
              )}
            >
              <div
                className="absolute right-10 top-10 z-50 text-[hsl(var(--tv-text-primary))] cursor-pointer"
                onClick={() => setOpen(!open)}
              >
                <X />
              </div>
              {children}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </>
  );
};

export const SidebarLink = ({
  link,
  className,
  ...props
}: {
  link: Links;
  className?: string;
  props?: LinkProps;
}) => {
  const { open, animate } = useSidebar();
  const [isActive, setIsActive] = React.useState(false);

  React.useEffect(() => {
    setIsActive(window.location.pathname === link.href);
  }, [link.href]);

  return (
    <Link
      href={link.href}
      className={cn(
        "flex items-center justify-center w-full h-12 relative group/sidebar transition-colors",
        isActive
          ? "bg-[hsl(var(--tv-surface-elevated))] border-l-2 border-[hsl(var(--tv-blue))]"
          : "hover:bg-[hsl(var(--tv-surface-elevated))]",
        className
      )}
      {...props}
    >
      <div className={cn(
        "transition-colors",
        isActive ? "text-[hsl(var(--tv-blue))]" : "text-[hsl(var(--tv-text-secondary))] group-hover/sidebar:text-[hsl(var(--tv-text-primary))]"
      )}>
        {link.icon}
      </div>
    </Link>
  );
};
